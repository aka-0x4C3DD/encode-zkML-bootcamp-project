import logging
import argparse
import os
import sys
from src.api.bluesky import BlueskyAPI
from src.ml.sentiment import EmotionAnalyzer
from src.zk.ezkl_integration import EZKLIntegrator  # Updated import path
import matplotlib.pyplot as plt
import numpy as np
from src.utils.setup_directories import setup_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_environment():
    """Set up necessary directories and environment."""
    # Use the new utility function
    directories = setup_directories()
    logging.info(f"Environment setup complete. Project root: {directories['project_root']}")
    return directories

def visualize_emotions(emotion_result, output_path="results/emotion_analysis.png"):
    """Create a visualization of emotion results."""
    labels = list(emotion_result['emotion_counts'].keys())
    values = list(emotion_result['emotion_counts'].values())
    
    # Define colors for each emotion
    colors = [
        '#FFD700',  # joy - Gold
        '#FF8C00',  # surprise - Dark Orange
        '#A9A9A9',  # neutral - Dark Gray
        '#1E90FF',  # sadness - Dodger Blue
        '#800080',  # fear - Purple
        '#FF0000',  # anger - Red
        '#006400',  # disgust - Dark Green
    ]
    
    # Create bar chart
    plt.figure(figsize=(12, 7))
    bars = plt.bar(labels, values, color=colors[:len(labels)])
    
    # Add labels and title
    plt.xlabel('Emotion')
    plt.ylabel('Number of Posts')
    plt.title('Emotion Analysis Results')
    
    # Add text labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{height}', ha='center', va='bottom')
    
    # Add overall emotion
    plt.figtext(0.5, 0.01, 
                f"Overall Emotion: {emotion_result['overall_emotion']}",
                ha="center", fontsize=12, 
                bbox={"facecolor":"orange", "alpha":0.2, "pad":5})
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path)
    logging.info(f"Emotion visualization saved to {output_path}")
    return output_path

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Privacy-preserving emotion analysis on Bluesky posts.')
    parser.add_argument('--question', type=str, help='Question to analyze emotions for')
    parser.add_argument('--username', type=str, help='Bluesky username')
    parser.add_argument('--password', type=str, help='Bluesky password')
    parser.add_argument('--export-model', action='store_true', help='Export model to ONNX format')
    parser.add_argument('--prepare-ezkl', action='store_true', help='Prepare EZKL environment')
    parser.add_argument('--visualize', action='store_true', help='Create visualization of emotion results')
    
    args = parser.parse_args()
    
    # Set up environment
    setup_environment()
    
    # Initialize emotion analyzer
    logging.info("Initializing emotion analyzer...")
    emotion_analyzer = EmotionAnalyzer()
    
    # Export model if requested
    if args.export_model:
        logging.info("Exporting model to ONNX format...")
        onnx_path = emotion_analyzer.export_to_onnx("models/emotion_model.onnx")
        if not onnx_path or not os.path.exists(onnx_path):
            logging.error(f"Model export failed, path not found: {onnx_path}")
            sys.exit(1)
        logging.info(f"Model exported to {onnx_path}")
    
    # Initialize EZKL integrator
    ezkl_integrator = EZKLIntegrator(model_path="models/emotion_model.onnx")
    
    # Prepare EZKL environment if requested
    if args.prepare_ezkl:
        logging.info("Preparing EZKL environment...")
        if not os.path.exists("models/emotion_model.onnx"):
            logging.error("Cannot prepare EZKL: model file doesn't exist at models/emotion_model.onnx")
            sys.exit(1)
        
        success = ezkl_integrator.prepare_model()
        if not success:
            logging.error("Failed to prepare EZKL environment")
            sys.exit(1)
        logging.info("EZKL environment prepared successfully")
    
    # If a question is provided, fetch posts and analyze emotions
    if args.question:
        logging.info(f"Processing question: {args.question}")
        
        # Initialize Bluesky API
        bluesky_api = BlueskyAPI(args.username, args.password)
        
        # Fetch posts
        logging.info("Fetching relevant posts...")
        posts = bluesky_api.fetch_posts_for_question(args.question)
        
        if not posts:
            logging.warning("No posts found for the given question")
            return
        
        logging.info(f"Found {len(posts)} relevant posts")
        
        # Analyze emotions
        logging.info("Analyzing emotions...")
        emotion_result = emotion_analyzer.get_aggregate_emotions(posts)
        
        # Create visualization if requested
        if args.visualize:
            visualize_emotions(emotion_result)
        
        # Display sample posts
        sample_size = min(3, len(posts))
        sample_posts = posts[:sample_size]
        
        # Display emotions analysis results
        print("\n--- Emotion Analysis Results ---")
        print(f"Question: {args.question}")
        print(f"Number of posts analyzed: {len(posts)}")
        print(f"Overall emotion: {emotion_result['overall_emotion']}")
        print("Emotion breakdown:")
        for emotion, count in emotion_result['emotion_counts'].items():
            print(f"  - {emotion}: {count}")
        
        print("\nSample posts:")
        for i, post in enumerate(sample_posts):
            emotion_data = emotion_result['emotions_data'][i]
            print(f"\n[{i+1}] [{emotion_data['dominant_emotion']}] {post[:100]}..." if len(post) > 100 else f"\n[{i+1}] [{emotion_data['dominant_emotion']}] {post}")
        
        print("\nNOTE: In a complete implementation, a zero-knowledge proof would be generated to verify the emotion analysis without revealing the posts.")

if __name__ == "__main__":
    main()
