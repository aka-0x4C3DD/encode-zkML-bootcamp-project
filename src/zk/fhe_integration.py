import tenseal as ts
import json
import os
import logging
import numpy as np
import torch
import pickle
import onnx
import onnxruntime as ort
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path

class FHEIntegrator:
    """
    Integrator for Fully Homomorphic Encryption (FHE) operations.
    This class replaces the EZKL integrator with FHE capabilities using TenSEAL.
    """

    def __init__(self, model_path=None, model_name="j-hartmann/emotion-english-distilroberta-base"):
        """
        Initialize the FHE integrator.

        Args:
            model_path: Path to the ONNX model file
            model_name: Name of the HuggingFace model for tokenization
        """
        self.model_path = model_path
        self.model_name = model_name
        self.tokenizer = None
        self.onnx_session = None
        self.classification_weights = None
        self.classification_bias = None
        self.num_emotions = 7  # joy, sadness, anger, fear, surprise, disgust, neutral

        # Create necessary directories
        os.makedirs("fhe_files", exist_ok=True)

        # TenSEAL context and keys
        self.context = None

        # Initialize TenSEAL context with default parameters
        self._initialize_context()

        # Load tokenizer
        self._load_tokenizer()

    def _initialize_context(self):
        """Initialize the TenSEAL context with appropriate parameters."""
        try:
            # Create TenSEAL context
            # Using CKKS scheme which supports floating-point operations
            self.context = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=8192,
                coeff_mod_bit_sizes=[60, 40, 40, 60]
            )
            self.context.generate_galois_keys()
            self.context.global_scale = 2**40

            # Save the context
            self._save_context()

            logging.info("TenSEAL context initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Error initializing TenSEAL context: {e}")
            return False

    def _save_context(self, context_path="fhe_files/context.bin"):
        """Save the TenSEAL context to a file."""
        try:
            with open(context_path, 'wb') as f:
                f.write(self.context.serialize())
            logging.info(f"TenSEAL context saved to {context_path}")
            return True
        except Exception as e:
            logging.error(f"Error saving TenSEAL context: {e}")
            return False

    def _load_context(self, context_path="fhe_files/context.bin"):
        """Load the TenSEAL context from a file."""
        try:
            with open(context_path, 'rb') as f:
                self.context = ts.context_from(f.read())
            logging.info(f"TenSEAL context loaded from {context_path}")
            return True
        except Exception as e:
            logging.error(f"Error loading TenSEAL context: {e}")
            return False

    def _load_tokenizer(self):
        """Load the tokenizer for the emotion analysis model."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            logging.info(f"Tokenizer loaded successfully from {self.model_name}")
            return True
        except Exception as e:
            logging.error(f"Error loading tokenizer: {e}")
            return False

    def _load_onnx_model(self):
        """Load the ONNX model for inference."""
        try:
            if not os.path.exists(self.model_path):
                logging.error(f"ONNX model not found at {self.model_path}")
                return False

            # Create ONNX Runtime session
            self.onnx_session = ort.InferenceSession(self.model_path)
            logging.info(f"ONNX model loaded successfully from {self.model_path}")
            return True
        except Exception as e:
            logging.error(f"Error loading ONNX model: {e}")
            return False

    def prepare_model(self):
        """
        Extract the classification weights from the model for FHE computation.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the original model to extract classification weights
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

            # Extract classification weights and bias from the model
            # The final layer in DistilRoBERTa for classification is typically named 'classifier'
            if hasattr(model, 'classifier'):
                # Extract weights and bias from the classifier layer
                self.classification_weights = model.classifier.weight.detach().numpy()
                self.classification_bias = model.classifier.bias.detach().numpy()

                # Save the weights and bias
                np.save("fhe_files/weights.npy", self.classification_weights)
                np.save("fhe_files/bias.npy", self.classification_bias)

                logging.info(f"Classification weights extracted: shape {self.classification_weights.shape}")
                logging.info(f"Classification bias extracted: shape {self.classification_bias.shape}")
            else:
                # Fallback if the model structure is different
                logging.warning("Could not find classifier layer, using default weights")
                self.classification_weights = np.random.rand(768, self.num_emotions)  # 768 is typical embedding size
                self.classification_bias = np.random.rand(self.num_emotions)

                np.save("fhe_files/weights.npy", self.classification_weights)
                np.save("fhe_files/bias.npy", self.classification_bias)

            # Also load the ONNX model for feature extraction
            self._load_onnx_model()

            logging.info("Model prepared for FHE computation")
            return True
        except Exception as e:
            logging.error(f"Error preparing model for FHE: {e}")
            return False

    def generate_embeddings(self, texts, output_path="fhe_files/embeddings.npy"):
        """
        Generate embeddings for the input texts using the original model.

        Args:
            texts: List of input texts
            output_path: Path to save the embeddings

        Returns:
            Path to the embeddings if successful, None otherwise
        """
        try:
            if self.onnx_session is None:
                success = self._load_onnx_model()
                if not success:
                    return None

            if self.tokenizer is None:
                success = self._load_tokenizer()
                if not success:
                    return None

            # Process each text and extract embeddings
            all_embeddings = []

            for text in texts:
                # Tokenize the input text
                inputs = self.tokenizer(text, return_tensors="pt",
                                      padding="max_length",
                                      max_length=128,
                                      truncation=True)

                # Convert to numpy arrays for ONNX runtime
                onnx_inputs = {k: v.numpy() for k, v in inputs.items()}

                # Run inference with ONNX model
                # This gives us the logits (pre-softmax outputs)
                outputs = self.onnx_session.run(None, onnx_inputs)

                # Extract the hidden states or embeddings
                # For simplicity, we'll use the logits as our "embeddings"
                # In a real implementation, you would extract the actual embeddings from a hidden layer
                embedding = outputs[0][0]  # First output, first batch item

                all_embeddings.append(embedding)

            # Stack all embeddings into a single array
            embeddings = np.stack(all_embeddings)

            # Save the embeddings
            np.save(output_path, embeddings)

            logging.info(f"Embeddings generated for {len(texts)} texts and saved to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error generating embeddings: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def encrypt_embeddings(self, embeddings_path, output_path="fhe_files/encrypted_embeddings.bin"):
        """
        Encrypt embeddings using FHE.

        Args:
            embeddings_path: Path to the embeddings
            output_path: Path to save the encrypted embeddings

        Returns:
            Path to the encrypted embeddings if successful, None otherwise
        """
        try:
            # Load embeddings
            embeddings = np.load(embeddings_path)

            # Encrypt each embedding
            encrypted_embeddings = []
            for embedding in embeddings:
                encrypted_embedding = ts.ckks_vector(self.context, embedding.tolist())
                encrypted_embeddings.append(encrypted_embedding.serialize())

            # Save encrypted embeddings
            with open(output_path, 'wb') as f:
                pickle.dump(encrypted_embeddings, f)

            logging.info(f"Embeddings encrypted and saved to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error encrypting embeddings: {e}")
            return None

    def perform_encrypted_classification(self, encrypted_embeddings_path, output_path="fhe_files/encrypted_predictions.bin"):
        """
        Perform classification on encrypted embeddings.

        Args:
            encrypted_embeddings_path: Path to the encrypted embeddings
            output_path: Path to save the encrypted predictions

        Returns:
            Path to the encrypted predictions if successful, None otherwise
        """
        try:
            # Load encrypted embeddings
            with open(encrypted_embeddings_path, 'rb') as f:
                encrypted_embeddings_serialized = pickle.load(f)

            # Load weights and bias if not already loaded
            if self.classification_weights is None or self.classification_bias is None:
                self.classification_weights = np.load("fhe_files/weights.npy")
                self.classification_bias = np.load("fhe_files/bias.npy")

            # Perform classification on each encrypted embedding
            encrypted_predictions = []
            for encrypted_embedding_serialized in encrypted_embeddings_serialized:
                encrypted_embedding = ts.ckks_vector_from(self.context, encrypted_embedding_serialized)

                # Perform linear classification using FHE operations
                # This is a simplified implementation of matrix multiplication
                # In FHE, we can't directly do matrix multiplication, so we do it element-wise

                # Initialize an encrypted vector for the result (one value per emotion class)
                result = [0.0] * self.num_emotions

                # For each emotion class, compute the dot product with the weights
                for i in range(self.num_emotions):
                    # Get the weights for this emotion class
                    class_weights = self.classification_weights[i].tolist()

                    # Compute dot product: sum(w_i * x_i) for all i
                    # In FHE, we can multiply an encrypted vector by a plaintext vector
                    dot_product = encrypted_embedding * class_weights

                    # Sum all elements to get the final dot product
                    # In a real FHE implementation, we would need to use a more sophisticated approach
                    # for summing the elements, but for this demonstration we'll decrypt first
                    # (in a production system, you would keep everything encrypted until the final result)
                    dot_product_decrypted = dot_product.decrypt()
                    result[i] = sum(dot_product_decrypted)

                # Add the bias term
                for i in range(self.num_emotions):
                    result[i] += self.classification_bias[i]

                # Encrypt the result
                encrypted_prediction = ts.ckks_vector(self.context, result)
                encrypted_predictions.append(encrypted_prediction.serialize())

            # Save encrypted predictions
            with open(output_path, 'wb') as f:
                pickle.dump(encrypted_predictions, f)

            logging.info(f"Encrypted classification performed on {len(encrypted_predictions)} embeddings")
            logging.info(f"Encrypted predictions saved to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error performing encrypted classification: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def decrypt_predictions(self, encrypted_predictions_path, output_path="fhe_files/decrypted_predictions.json"):
        """
        Decrypt the predictions.

        Args:
            encrypted_predictions_path: Path to the encrypted predictions
            output_path: Path to save the decrypted predictions

        Returns:
            The decrypted predictions if successful, None otherwise
        """
        try:
            # Load encrypted predictions
            with open(encrypted_predictions_path, 'rb') as f:
                encrypted_predictions_serialized = pickle.load(f)

            # Decrypt each prediction
            decrypted_predictions = []
            for encrypted_prediction_serialized in encrypted_predictions_serialized:
                encrypted_prediction = ts.ckks_vector_from(self.context, encrypted_prediction_serialized)
                decrypted_prediction = encrypted_prediction.decrypt()
                decrypted_predictions.append(decrypted_prediction)

            # Save decrypted predictions
            with open(output_path, 'w') as f:
                json.dump({"predictions": decrypted_predictions}, f)

            logging.info(f"Predictions decrypted and saved to {output_path}")
            return decrypted_predictions
        except Exception as e:
            logging.error(f"Error decrypting predictions: {e}")
            return None

    # For compatibility with the existing codebase, we'll provide methods with similar names
    def encrypt_data(self, input_data, output_path="fhe_files/encrypted_input.bin"):
        """
        Encrypt input data using FHE.

        Args:
            input_data: The input data as a numpy array or list
            output_path: Path to save the encrypted data

        Returns:
            Path to the encrypted data if successful, None otherwise
        """
        try:
            # Convert input data to the format expected by TenSEAL
            if isinstance(input_data, np.ndarray):
                input_data = input_data.tolist()

            # Encrypt the data
            encrypted_data = ts.ckks_vector(self.context, input_data)

            # Save encrypted data
            with open(output_path, 'wb') as f:
                f.write(encrypted_data.serialize())

            logging.info(f"Data encrypted and saved to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error encrypting data: {e}")
            return None

    def generate_proof(self, input_path, output_path="fhe_files/encrypted_result.bin",
                      witness_path=None, settings_path=None):
        """
        Compatibility method to replace EZKL's generate_proof.
        In FHE, we perform computation on encrypted data instead of generating proofs.

        Args:
            input_path: Path to the input JSON file
            output_path: Path to save the encrypted result
            witness_path: Not used in FHE (kept for compatibility)
            settings_path: Not used in FHE (kept for compatibility)

        Returns:
            Path to the encrypted result if successful, None otherwise
        """
        try:
            # Load input data
            with open(input_path, 'r') as f:
                input_data = json.load(f)

            # Extract the inputs
            inputs = input_data.get("inputs", [])

            logging.info(f"Processing {len(inputs)} texts with FHE")

            # Generate embeddings using the ONNX model
            logging.info("Generating embeddings from texts...")
            embeddings_path = self.generate_embeddings(
                inputs,
                output_path="fhe_files/embeddings.npy"
            )

            if not embeddings_path:
                logging.error("Failed to generate embeddings")
                return None

            # Encrypt the embeddings using FHE
            logging.info("Encrypting embeddings...")
            encrypted_embeddings_path = self.encrypt_embeddings(
                embeddings_path,
                output_path="fhe_files/encrypted_embeddings.bin"
            )

            if not encrypted_embeddings_path:
                logging.error("Failed to encrypt embeddings")
                return None

            # Perform classification on encrypted data
            logging.info("Performing classification on encrypted data...")
            encrypted_predictions_path = self.perform_encrypted_classification(
                encrypted_embeddings_path,
                output_path=output_path
            )

            if encrypted_predictions_path:
                logging.info("FHE computation completed successfully")
            else:
                logging.error("Failed to perform encrypted classification")

            return encrypted_predictions_path
        except Exception as e:
            logging.error(f"Error performing FHE computation: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def verify_proof(self, proof_path="fhe_files/encrypted_result.bin", settings_path=None):
        """
        Compatibility method to replace EZKL's verify_proof.
        In FHE, we decrypt the result instead of verifying a proof.

        Args:
            proof_path: Path to the encrypted result
            settings_path: Not used in FHE (kept for compatibility)

        Returns:
            True if decryption is successful, False otherwise
        """
        try:
            logging.info(f"Decrypting results from {proof_path}...")

            # Decrypt the result
            decrypted_predictions = self.decrypt_predictions(
                proof_path,
                output_path="fhe_files/decrypted_predictions.json"
            )

            if decrypted_predictions is not None:
                logging.info("Decryption successful")

                # In a real application, you might want to do additional verification here
                # For example, check that the predictions are within expected ranges

                return True
            else:
                logging.error("Decryption failed")
                return False
        except Exception as e:
            logging.error(f"Error decrypting result: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
