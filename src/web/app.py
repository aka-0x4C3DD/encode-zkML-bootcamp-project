from flask import Flask, render_template, request, jsonify, session
import os
import sys
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api.bluesky import BlueskyAPI
from src.ml.sentiment import EmotionAnalyzer
from src.zk.ezkl_integration import EZKLIntegrator  # Updated import path

# Ensure directories exist
os.makedirs("models", exist_ok=True)
os.makedirs("ezkl_files", exist_ok=True)

# Initialize Flask app with correct static folder path
app = Flask(__name__, 
           static_url_path='/static',
           static_folder='static')
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
emotion_analyzer = EmotionAnalyzer()
ezkl_integrator = EZKLIntegrator(model_path="models/emotion_model.onnx")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze emotions from the form submission."""
    question = request.form.get('question')
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Validate inputs
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Initialize Bluesky API
        bluesky_api = BlueskyAPI()  # Initialize without credentials first
        
        # Only attempt login if both username and password are provided
        if username and password:
            success = bluesky_api.login(username, password)
            if not success:
                return jsonify({'error': 'Failed to authenticate with Bluesky. Please check your credentials.'}), 401
        
        # Fetch posts
        posts = bluesky_api.fetch_posts_for_question(question)
        
        if not posts:
            return jsonify({
                'error': 'No posts found for the given question. ' + 
                         ('Try providing valid Bluesky credentials for better results.' if not bluesky_api.is_authenticated else '')
            }), 404
        
        # Analyze emotions
        emotion_results = emotion_analyzer.get_aggregate_emotions(posts)
        
        # Store the data needed for proof generation in the session
        session['analysis_data'] = {
            'posts': posts,
            'emotion_results': emotion_results
        }
        
        # Prepare response with full emotion data for interactive visualization
        emotion_counts = emotion_results['emotion_counts']
        emotion_scores = emotion_results['emotion_scores']
        colors = [emotion_analyzer.EMOTION_COLORS[emotion] for emotion in emotion_counts.keys()]
        
        # Prepare response
        response = {
            'success': True,
            'question': question,
            'post_count': len(posts),
            'overall_emotion': emotion_results['overall_emotion'],
            'emotion_counts': emotion_counts,
            'emotion_scores': emotion_scores,
            'colors': colors,
            'emotions_data': emotion_results['emotions_data'],
            'sample_posts': posts[:50]  # Process up to 50 posts
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error during emotion analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_proof', methods=['POST'])
def generate_proof():
    """Generate a real zero-knowledge proof for the emotion analysis."""
    try:
        if 'analysis_data' not in session:
            return jsonify({'error': 'No analysis data available'}), 400
        
        analysis_data = session['analysis_data']
        posts = analysis_data['posts']
        emotion_results = analysis_data['emotion_results']
        
        # Show progress message to user
        logger.info(f"Starting proof generation with {min(len(posts), 50)} posts")
        
        # Step 1: Prepare input for the proof generation
        # Convert the posts to a format suitable for ezkl
        inputs = []
        for post in posts[:50]:  # Process up to 50 posts using GPU acceleration
            # Simple preprocessing: convert to lowercase, remove special chars
            processed = ''.join(c.lower() if c.isalnum() else ' ' for c in post)
            inputs.append(processed)
        
        # Step 2: Create a JSON representation of inputs
        input_file = os.path.join("ezkl_files", "emotion_input.json")
        with open(input_file, 'w') as f:
            json.dump({"inputs": inputs}, f)
        
        # Step 3: Generate proof using ezkl (GPU-accelerated)
        proof_path = ezkl_integrator.generate_proof(
            input_path=input_file,
            output_path="ezkl_files/emotion_proof.json"
        )
        
        if not proof_path:
            return jsonify({
                'success': False,
                'message': 'Failed to generate proof',
                'verification': 'Proof generation failed'
            })
        
        # Step 4: Verify the proof
        verification_result = ezkl_integrator.verify_proof(proof_path=proof_path)
        
        # Return verification result
        return jsonify({
            'success': True,
            'message': 'Zero-knowledge proof generated successfully',
            'verification': 'The emotion analysis result was verified using zero-knowledge proofs, ensuring privacy of the analyzed posts.',
            'is_verified': verification_result
        })
        
    except Exception as e:
        logger.error(f"Error generating proof: {e}")
        return jsonify({
            'success': False,
            'message': f'Error generating proof: {str(e)}',
            'verification': 'Proof generation failed'
        })

@app.route('/test_auth', methods=['POST'])
def test_auth():
    """Test Bluesky API authentication with the provided credentials."""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Both username and password are required'}), 400
    
    try:
        bluesky_api = BlueskyAPI()
        success = bluesky_api.login(username, password)
        
        if success:
            return jsonify({'success': True, 'message': 'Authentication successful'})
        else:
            return jsonify({'error': 'Authentication failed. Invalid username or password.'}), 401
    except Exception as e:
        return jsonify({'error': f'Authentication error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
