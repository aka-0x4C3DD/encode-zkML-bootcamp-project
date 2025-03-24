from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import onnx
import numpy as np
import logging
import os
import json
from typing import List, Dict, Any, Tuple

class EmotionAnalyzer:
    """Enhanced emotion analyzer using a more nuanced emotion detection model."""
    
    # Map of emotion labels to color codes for visualization
    EMOTION_COLORS = {
        'joy': '#FFD700',      # Gold
        'surprise': '#FF8C00', # Dark Orange
        'neutral': '#A9A9A9',  # Dark Gray
        'sadness': '#1E90FF',  # Dodger Blue
        'fear': '#800080',     # Purple
        'anger': '#FF0000',    # Red
        'disgust': '#006400',  # Dark Green
    }
    
    def __init__(self, model_name="j-hartmann/emotion-english-distilroberta-base"):
        self.model_name = model_name
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.emotion_pipeline = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                return_all_scores=True
            )
            logging.info(f"Emotion analysis model {model_name} loaded successfully")
        except Exception as e:
            logging.error(f"Error loading emotion analysis model: {e}")
            raise

    def analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze emotions in a list of texts.
        Returns a list of dictionaries with scores for each emotion.
        """
        if not texts:
            return []
        
        try:
            results = self.emotion_pipeline(texts)
            # Format results to be more usable
            formatted_results = []
            
            for item in results:
                # For a single text, we get a list of dicts with label and score
                emotion_scores = {emotion['label']: emotion['score'] for emotion in item}
                # Find the dominant emotion (highest score)
                dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
                
                formatted_results.append({
                    'emotions': emotion_scores,
                    'dominant_emotion': dominant_emotion[0],
                    'dominant_score': dominant_emotion[1]
                })
                
            return formatted_results
        except Exception as e:
            logging.error(f"Error during emotion analysis: {e}")
            return []

    def get_aggregate_emotions(self, texts: List[str]) -> Dict[str, Any]:
        """
        Get aggregate emotions for a list of texts.
        Returns:
        - overall_emotion: dominant emotion across all texts
        - emotion_counts: counts of each emotion category
        - emotion_scores: average scores for each emotion
        """
        if not texts:
            return {
                'overall_emotion': 'neutral',
                'emotion_counts': {emotion: 0 for emotion in self.EMOTION_COLORS.keys()},
                'emotion_scores': {emotion: 0 for emotion in self.EMOTION_COLORS.keys()},
                'emotions_data': []
            }
        
        results = self.analyze(texts)
        
        # Count emotions and collect scores
        emotion_counts = {emotion: 0 for emotion in self.EMOTION_COLORS.keys()}
        emotion_scores_sum = {emotion: 0.0 for emotion in self.EMOTION_COLORS.keys()}
        emotion_data = []
        
        for result in results:
            # Update the dominant emotion count
            dominant_emotion = result['dominant_emotion']
            emotion_counts[dominant_emotion] += 1
            
            # Sum up scores for each emotion
            for emotion, score in result['emotions'].items():
                emotion_scores_sum[emotion] += score
            
            # Store individual emotion data for visualization
            emotion_data.append({
                'text_snippet': texts[results.index(result)][:100] + ('...' if len(texts[results.index(result)]) > 100 else ''),
                'emotions': result['emotions'],
                'dominant_emotion': dominant_emotion
            })
        
        # Calculate average scores
        emotion_scores_avg = {
            emotion: score / len(texts) 
            for emotion, score in emotion_scores_sum.items()
        }
        
        # Determine overall dominant emotion
        overall_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        if emotion_counts[overall_emotion] == 0:
            overall_emotion = 'neutral'
            
        return {
            'overall_emotion': overall_emotion,
            'emotion_counts': emotion_counts,
            'emotion_scores': emotion_scores_avg,
            'emotions_data': emotion_data
        }
    
    def export_to_onnx(self, output_path="model.onnx") -> str:
        """Export the model to ONNX format for use with ezKL."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Get model components and device
            tokenizer = self.tokenizer
            model = self.model
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            model = model.to(device)
            
            # Create dummy inputs with FIXED shapes - crucial for EZKL compatibility
            dummy_text = "This is a test input for ONNX export"
            encoded_inputs = tokenizer(dummy_text, return_tensors="pt", 
                                      padding="max_length", 
                                      max_length=128,
                                      truncation=True)
            encoded_inputs = {k: v.to(device) for k, v in encoded_inputs.items()}
            
            # Remove dynamic_axes but keep current opset version
            torch.onnx.export(
                model,
                tuple(encoded_inputs.values()),
                output_path,
                input_names=list(encoded_inputs.keys()),
                output_names=["output"],
                do_constant_folding=True,
                opset_version=14,  # Keep current version 
                export_params=True
            )
            
            # Verify the export
            onnx.checker.check_model(onnx.load(output_path))
            logging.info(f"Model exported to {output_path}")
            
            return output_path
        except Exception as e:
            logging.error(f"Error exporting model to ONNX: {e}")
            return None
