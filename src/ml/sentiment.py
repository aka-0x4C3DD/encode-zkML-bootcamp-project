from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import onnx
import numpy as np
import logging
import os
import json
from typing import List, Dict, Any, Tuple

class SentimentAnalyzer:
    def __init__(self, model_name="tabularisai/multilingual-sentiment-analysis"):
        self.model_name = model_name
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name
            )
            logging.info(f"Sentiment analysis model {model_name} loaded successfully")
        except Exception as e:
            logging.error(f"Error loading sentiment analysis model: {e}")
            raise

    def analyze(self, texts):
        """
        Analyze sentiment of a list of texts.
        Returns a list of dictionaries with 'label' and 'score' keys.
        """
        if not texts:
            return []
        
        try:
            results = self.sentiment_pipeline(texts)
            return results
        except Exception as e:
            logging.error(f"Error during sentiment analysis: {e}")
            return []

    def get_aggregate_sentiment(self, texts):
        """
        Get aggregate sentiment for a list of texts.
        Returns:
        - overall_sentiment: 'positive', 'negative', or 'neutral'
        - average_score: average confidence score
        - sentiment_counts: counts of each sentiment category
        """
        if not texts:
            return {
                'overall_sentiment': 'neutral',
                'average_score': 0.5,
                'sentiment_counts': {'positive': 0, 'neutral': 0, 'negative': 0}
            }
        
        results = self.analyze(texts)
        
        # Count sentiments
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        scores = []
        
        for result in results:
            label = result['label'].lower()
            score = result['score']
            
            if label == 'positive':
                sentiment_counts['positive'] += 1
                scores.append(score)
            elif label == 'negative':
                sentiment_counts['negative'] += 1
                scores.append(1 - score)  # Invert score for negative sentiment
            else:  # neutral
                sentiment_counts['neutral'] += 1
                scores.append(0.5)  # Neutral score
        
        # Calculate average score (higher means more positive)
        average_score = sum(scores) / len(scores) if scores else 0.5
        
        # Determine overall sentiment
        if sentiment_counts['positive'] > sentiment_counts['negative'] and sentiment_counts['positive'] > sentiment_counts['neutral']:
            overall_sentiment = 'positive'
        elif sentiment_counts['negative'] > sentiment_counts['positive'] and sentiment_counts['negative'] > sentiment_counts['neutral']:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
            
        return {
            'overall_sentiment': overall_sentiment,
            'average_score': average_score,
            'sentiment_counts': sentiment_counts
        }
    
    def export_to_onnx(self, output_path="model.onnx"):
        """
        Export the model to ONNX format for use with ezKL.
        """
        try:
            # This is a simplified approach - in reality, exporting a transformer model to ONNX
            # requires more complex handling of inputs and outputs
            model = self.sentiment_pipeline.model
            
            # Create dummy input
            tokenizer = self.sentiment_pipeline.tokenizer
            dummy_input = tokenizer("This is a test", return_tensors="pt")
            
            # Export to ONNX
            torch.onnx.export(
                model,
                tuple(dummy_input.values()),
                output_path,
                opset_version=12,
                input_names=['input_ids', 'attention_mask'],
                output_names=['logits'],
                dynamic_axes={
                    'input_ids': {0: 'batch_size', 1: 'sequence_length'},
                    'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
                    'logits': {0: 'batch_size'}
                }
            )
            
            logging.info(f"Model exported to ONNX format at {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error exporting model to ONNX: {e}")
            return None

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
        """
        Export the model to ONNX format for use with ezKL.
        This is a complete implementation for properly exporting transformer models.
        """
        try:
            # Create proper model export directory
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Get model inputs
            tokenizer = self.tokenizer
            model = self.model
            
            # Create proper dummy inputs for the model
            dummy_text = "This is a test input for ONNX export"
            encoded_inputs = tokenizer(dummy_text, return_tensors="pt", padding="max_length", max_length=128)
            
            # Get input names dynamically
            input_names = list(encoded_inputs.keys())
            
            # Define dynamic axes for the inputs and outputs
            dynamic_axes = {}
            for input_name in input_names:
                dynamic_axes[input_name] = {0: "batch_size", 1: "sequence_length"}
            dynamic_axes["output"] = {0: "batch_size"}
            
            # Export to ONNX with proper configuration
            torch.onnx.export(
                model,
                tuple(encoded_inputs.values()),
                output_path,
                input_names=input_names,
                output_names=["output"],
                dynamic_axes=dynamic_axes,
                do_constant_folding=True,
                opset_version=12,
                export_params=True
            )
            
            # Save tokenizer configuration alongside the model
            tokenizer_config_path = os.path.join(os.path.dirname(output_path), "tokenizer_config.json")
            with open(tokenizer_config_path, "w") as f:
                # Save basic tokenizer configuration for preprocessing
                config = {
                    "model_name": self.model_name,
                    "max_length": 128,
                    "padding": "max_length",
                    "truncation": True
                }
                json.dump(config, f)
            
            # Verify the exported model
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)
            
            logging.info(f"Model exported to ONNX format at {output_path}")
            logging.info(f"Tokenizer config saved at {tokenizer_config_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error exporting model to ONNX: {e}")
            return None

    def predict_with_onnx(self, text: str, onnx_path: str) -> Dict[str, float]:
        """
        Run prediction using the exported ONNX model.
        This is for verifying that the ONNX export worked properly.
        """
        import onnxruntime as ort
        
        # Load tokenizer configuration
        tokenizer_config_path = os.path.join(os.path.dirname(onnx_path), "tokenizer_config.json")
        with open(tokenizer_config_path, "r") as f:
            tokenizer_config = json.load(f)
        
        # Preprocess input
        inputs = self.tokenizer(
            text, 
            return_tensors="np",
            padding=tokenizer_config["padding"],
            max_length=tokenizer_config["max_length"],
            truncation=tokenizer_config["truncation"]
        )
        
        # Create ONNX Runtime session
        session = ort.InferenceSession(onnx_path)
        
        # Prepare input dict for ONNX
        onnx_inputs = {name: inputs[name].numpy() for name in inputs}
        
        # Run inference
        outputs = session.run(None, onnx_inputs)
        
        # Process outputs to match the original model's output format
        logits = outputs[0][0]
        scores = torch.nn.functional.softmax(torch.tensor(logits), dim=0).numpy()
        
        # Get emotion labels from the original model's config
        id2label = self.model.config.id2label
        
        # Format results
        result = {id2label[i]: float(scores[i]) for i in range(len(scores))}
        return result
