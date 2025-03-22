#!/bin/bash
# File: setup_and_run.sh

# Enable verbose error logging
set -e           # Exit immediately if a command exits with non-zero status
exec 3>&1        # Save stdout to file descriptor 3
exec 4>&2        # Save stderr to file descriptor 4
LOG_FILE="setup_log.txt"
touch $LOG_FILE
exec 1> >(tee -a "$LOG_FILE") # Redirect stdout to log file while also displaying it
exec 2> >(tee -a "$LOG_FILE" >&2) # Redirect stderr to log file while also displaying it

echo "==================================================="
echo "Privacy-Preserving Emotion Analysis Setup"
echo "==================================================="
echo "Setup started at: $(date)"
echo "Verbose logs will be saved to $LOG_FILE"

# Check if Python is installed
echo "Checking for Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8 or higher." >&4
    exit 1
else
    python_version=$(python3 --version)
    echo "Found $python_version"
fi

# Upgrade pip
echo
echo "Step 0: Upgrading pip..."
python3 -m pip install --upgrade pip -v || {
    echo "WARNING: Failed to upgrade pip, but continuing setup." >&4
}

# Create virtual environment
echo
echo "Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv || {
        echo "ERROR: Failed to create virtual environment." >&4
        exit 1
    }
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || {
    echo "ERROR: Failed to activate virtual environment." >&4
    exit 1
}

# Install wheel and setuptools
echo
echo "Step 2: Installing dependencies..."
echo "Installing wheel and setuptools first..."
pip install wheel setuptools --upgrade -v || {
    echo "WARNING: Failed to install wheel and setuptools." >&4
}

# Install spaCy
echo
echo "Installing spaCy and downloading language model..."
pip install spacy --no-build-isolation -v || {
    echo "==================================================="
    echo "ERROR: Failed to install spaCy." >&4
    echo "You may need to install build dependencies:"
    echo "Ubuntu/Debian: sudo apt-get install build-essential python3-dev"
    echo "Fedora/RHEL/CentOS: sudo dnf install gcc-c++ python3-devel"
    echo "macOS: xcode-select --install"
    echo
    echo "After installing the dependencies, run this script again."
    echo "==================================================="
    exit 1
}

# Download spaCy language model
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm -v || {
    echo "WARNING: Failed to download spaCy language model, but continuing setup." >&4
}

# Install remaining dependencies
echo
echo "Installing remaining dependencies..."
pip install -r requirements.txt --no-deps -v || {
    echo "WARNING: Some dependencies may not be installed correctly." >&4
    echo "You can try installing them manually if you encounter issues." >&4
}

# Export model
echo
echo "Step 3: Exporting emotion analysis model..."
if [ ! -f "models/emotion_model.onnx" ]; then
    echo "Exporting model to ONNX format..."
    python -m src.main --export-model || {
        echo "ERROR: Failed to export model." >&4
        exit 1
    }
else
    echo "Model already exists, skipping export."
fi

# Prepare EZKL environment
echo
echo "Step 4: Preparing EZKL environment..."
if [ ! -f "ezkl_files/circuit.ezkl" ]; then
    echo "Setting up EZKL environment..."
    python -m src.main --prepare-ezkl || {
        echo "ERROR: Failed to prepare EZKL environment." >&4
        exit 1
    }
else
    echo "EZKL environment already prepared, skipping setup."
fi

# Start web application
echo
echo "==================================================="
echo "Setup complete! Starting web application..."
echo "==================================================="
echo
echo "The application will be available at http://localhost:5000"
echo "Press Ctrl+C to stop the application."
echo

# Restore original stdout and stderr before running the app
# This ensures app output doesn't go to the log file
exec 1>&3
exec 2>&4

# Run the application
python run_web_app.py

# Final message when the app stops
echo
echo "Application terminated. See $LOG_FILE for setup logs."