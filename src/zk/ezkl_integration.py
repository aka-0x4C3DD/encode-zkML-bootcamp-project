import ezkl
import json
import os
import logging
from pathlib import Path
import numpy as np
import torch  # Add this import at the top

class EZKLIntegrator:
    def __init__(self, model_path=None):
        """
        Initialize the EZKL integrator.
        
        Args:
            model_path: Path to the ONNX model file
        """
        self.model_path = model_path
        self.circuit_path = None
        self.pk_path = None
        self.vk_path = None
        self.srs_path = None
        
        # Create necessary directories
        os.makedirs("ezkl_files", exist_ok=True)

    def prepare_model(self, model_path=None):
        """Prepare the model for use with EZKL."""
        if model_path:
            self.model_path = model_path
        
        # Create required directory
        os.makedirs("ezkl_files", exist_ok=True)
        
        try:
            logging.warning("Using mock EZKL integration for demonstration purposes")
            
            # Create mock files for demonstration
            self.circuit_path = os.path.join("ezkl_files", "circuit.ezkl")
            self.srs_path = os.path.join("ezkl_files", "kzg.srs")
            self.pk_path = os.path.join("ezkl_files", "pk.key")
            self.vk_path = os.path.join("ezkl_files", "vk.key")
            
            # Create empty files for testing
            for path in [self.circuit_path, self.srs_path, self.pk_path, self.vk_path]:
                with open(path, 'w') as f:
                    f.write("MOCK FILE FOR DEMO")
            
            # Add the same for proof generation and verification
            def mock_generate_proof(*args, **kwargs):
                proof_path = os.path.join("ezkl_files", "proof.json")
                with open(proof_path, 'w') as f:
                    f.write('{"mock":"proof"}')
                return proof_path
            
            def mock_verify_proof(*args, **kwargs):
                return True
                
            # Monkey patch the methods
            self.generate_proof = mock_generate_proof
            self.verify_proof = mock_verify_proof
            
            return True
        except Exception as e:
            logging.error(f"Error preparing model for EZKL: {e}")
            return False
    
    def prepare_input(self, input_data, input_path="ezkl_files/input.json"):
        """
        Prepare input data for EZKL.
        
        Args:
            input_data: The input data as a numpy array or list
            input_path: Path to save the input JSON file
        """
        try:
            # Convert input data to the format expected by EZKL
            if isinstance(input_data, np.ndarray):
                input_data = input_data.tolist()
            
            # Create a simple dictionary structure for the input
            input_dict = {"input_0": input_data}
            
            # Save to JSON
            with open(input_path, 'w') as f:
                json.dump(input_dict, f)
            
            logging.info(f"Input data prepared and saved to {input_path}")
            return input_path
        except Exception as e:
            logging.error(f"Error preparing input data: {e}")
            return None
    
    def generate_proof(self, input_path, output_path="ezkl_files/proof.json", 
                      witness_path="ezkl_files/witness.json", settings_path="ezkl_files/settings.json"):
        """
        Generate a zero-knowledge proof for the given input.
        
        Args:
            input_path: Path to the input JSON file
            output_path: Path to save the output proof
            witness_path: Path to save the witness
            settings_path: Path to the settings JSON file
        
        Returns:
            Path to the proof file if successful, None otherwise
        """
        try:
            # Update settings for GPU optimization
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            
            # Check if GPU is available
            if torch.cuda.is_available():
                logging.info("GPU acceleration enabled for proof generation")
                settings['run_args'] = settings.get('run_args', {})
                settings['run_args']['accelerate'] = True
                settings['run_args']['device'] = 'cuda'
                
                # Save updated settings
                with open(settings_path, 'w') as f:
                    json.dump(settings, f, indent=2)
            
            # Generate witness
            ezkl.gen_witness(self.circuit_path, input_path, witness_path, settings_path)
            
            # Generate proof
            ezkl.prove(self.circuit_path, witness_path, self.pk_path, output_path, self.srs_path, settings_path)
            
            logging.info(f"Proof generated successfully and saved to {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error generating proof: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def verify_proof(self, proof_path="ezkl_files/proof.json", settings_path="ezkl_files/settings.json"):
        """
        Verify a zero-knowledge proof.
        
        Args:
            proof_path: Path to the proof file
            settings_path: Path to the settings JSON file
        
        Returns:
            True if verification is successful, False otherwise
        """
        try:
            result = ezkl.verify(proof_path, self.vk_path, self.srs_path, settings_path)
            if result:
                logging.info("Proof verification successful")
            else:
                logging.warning("Proof verification failed")
            return result
        except Exception as e:
            logging.error(f"Error verifying proof: {e}")
            return False
    
    def tokenize_and_prepare_input(self, text, tokenizer):
        """
        Tokenize text and prepare it for the model.
        
        Args:
            text: The text to tokenize
            tokenizer: The tokenizer to use
        
        Returns:
            Path to the prepared input file
        """
        try:
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt")
            
            # Convert to numpy arrays
            input_ids = inputs["input_ids"].numpy()
            attention_mask = inputs["attention_mask"].numpy()
            
            # Prepare inputs
            input_dict = {
                "input_ids": input_ids.tolist(),
                "attention_mask": attention_mask.tolist()
            }
            
            # Save to file
            input_path = "ezkl_files/input.json"
            with open(input_path, 'w') as f:
                json.dump(input_dict, f)
            
            return input_path
        except Exception as e:
            logging.error(f"Error tokenizing and preparing input: {e}")
            return None
