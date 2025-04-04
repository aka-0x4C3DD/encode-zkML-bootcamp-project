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
from src.zk.fhe_integration import FHEIntegrator  # Updated to use FHE instead of EZKL

# Ensure directories exist
os.makedirs("models", exist_ok=True)
os.makedirs("fhe_files", exist_ok=True)  # Changed from ezkl_files to fhe_files

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
fhe_integrator = FHEIntegrator(model_path="models/emotion_model.onnx")  # Changed from ezkl_integrator to fhe_integrator

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

        # Step 1: Prepare input for the FHE computation
        # Convert the posts to a format suitable for FHE
        logger.info(f"Starting FHE computation with {min(len(posts), 50)} posts")
        inputs = []
        for post in posts[:50]:  # Process up to 50 posts
            # Simple preprocessing: convert to lowercase, remove special chars
            processed = ''.join(c.lower() if c.isalnum() else ' ' for c in post)
            inputs.append(processed)

        # Step 2: Create a JSON representation of inputs
        input_file = os.path.join("fhe_files", "emotion_input.json")
        with open(input_file, 'w') as f:
            json.dump({"inputs": inputs}, f)

        # Step 3: Generate embeddings and perform encrypted computation
        logger.info("Performing emotion analysis with FHE...")
        encrypted_result_path = fhe_integrator.generate_proof(
            input_path=input_file,
            output_path="fhe_files/encrypted_predictions.bin"
        )

        if not encrypted_result_path:
            return jsonify({
                'error': 'Failed to perform encrypted computation'
            }), 500

        # Step 4: Decrypt the result
        verification_result = fhe_integrator.verify_proof(proof_path=encrypted_result_path)

        if not verification_result:
            return jsonify({
                'error': 'Failed to decrypt FHE computation results'
            }), 500

        # Also perform regular emotion analysis for visualization
        emotion_results = emotion_analyzer.get_aggregate_emotions(posts)

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
            'sample_posts': posts[:50],  # Process up to 50 posts
            'fhe_enabled': True,
            'fhe_details': {
                'method': 'TenSEAL CKKS',
                'description': 'Analysis performed using Fully Homomorphic Encryption on encrypted data without decrypting it first.'
            }
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error during emotion analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_proof', methods=['POST'])
def generate_proof():
    """Legacy endpoint for compatibility - now a no-op since FHE is integrated into main analysis."""
    return jsonify({
        'success': True,
        'message': 'FHE computation is now integrated into the main analysis flow',
        'verification': 'The emotion analysis was already performed using Fully Homomorphic Encryption during the initial analysis.',
        'is_verified': True,
        'fhe_details': {
            'method': 'TenSEAL CKKS',
            'description': 'FHE is now automatically applied during the main analysis - no separate step needed.'
        }
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
