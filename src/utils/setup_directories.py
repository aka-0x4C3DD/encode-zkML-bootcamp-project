import os
import logging

def setup_directories():
    """Set up necessary directories using absolute paths."""
    # Get the absolute path to the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up two levels
    
    # Define absolute paths for all required directories
    models_dir = os.path.join(project_root, "models")
    ezkl_dir = os.path.join(project_root, "ezkl_files")
    results_dir = os.path.join(project_root, "results")
    
    # Create directories if they don't exist
    for directory in [models_dir, ezkl_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Ensured directory exists: {directory}")
    
    return {
        'models_dir': models_dir,
        'ezkl_dir': ezkl_dir,
        'results_dir': results_dir,
        'project_root': project_root
    }