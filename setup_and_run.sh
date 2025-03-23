#!/bin/bash
# File: setup_and_run.sh

# Create a timestamped log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="setup_log_${TIMESTAMP}.txt"
touch $LOG_FILE
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Setup started, creating log file: $LOG_FILE" > $LOG_FILE

# Enable error handling with traps
set -e  # Exit immediately if a command exits with non-zero status
trap 'echo "[$(date "+%Y-%m-%d %H:%M:%S")] ERROR: Command failed at line $LINENO with exit code $?" | tee -a "$LOG_FILE"' ERR

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to log with timestamp and category
log() {
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local category=$1
  local message=$2
  local color=$NC
  
  case $category in
    "ERROR")
      color=$RED
      ;;
    "WARNING")
      color=$YELLOW
      ;;
    "SUCCESS")
      color=$GREEN
      ;;
    *)
      ;;
  esac
  
  echo -e "[$timestamp] ${color}${category}:${NC} $message" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
  local exit_code=$1
  local error_message=$2
  local suggestion=$3
  
  if [ $exit_code -ne 0 ]; then
    log "ERROR" "$error_message"
    if [ ! -z "$suggestion" ]; then
      log "INFO" "$suggestion"
    fi
    return 1
  fi
  return 0
}

# Save original stdout and stderr
exec 3>&1
exec 4>&2

# Redirect stdout and stderr to tee with timestamps
exec > >(while read line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line" | tee -a "$LOG_FILE"; done)
exec 2> >(while read line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $line" | tee -a "$LOG_FILE" >&2; done)

log "SYSTEM" "==================================================="
log "SYSTEM" "Privacy-Preserving Emotion Analysis Setup"
log "SYSTEM" "==================================================="
log "SYSTEM" "Verbose logs will be saved to $LOG_FILE"

# Check if Python is installed
log "SYSTEM" "Checking for Python installation..."
if ! command -v python3 &> /dev/null; then
    log "ERROR" "Python not found. Please install Python 3.8 or higher."
    log "INFO" "On Ubuntu/Debian: sudo apt install python3.8"
    log "INFO" "On macOS: brew install python@3.8"
    exit 1
else
    python_version=$(python3 --version)
    log "SUCCESS" "Found $python_version"
fi

# Upgrade pip
log "SYSTEM" "Step 0: Upgrading pip..."
python3 -m pip install --upgrade pip -v || handle_error $? "Failed to upgrade pip" "Continuing setup, but you might face issues with package installation"

# Create virtual environment
log "SYSTEM" "Step 1: Creating virtual environment..."
if [ ! -d "venv" ]; then
    log "SYSTEM" "Creating new virtual environment..."
    python3 -m venv venv
    handle_error $? "Failed to create virtual environment" "Check if python3-venv is installed. On Ubuntu/Debian run: sudo apt install python3-venv"
    log "SUCCESS" "Virtual environment created"
else
    log "SYSTEM" "Virtual environment already exists."
fi

# Activate virtual environment
log "SYSTEM" "Activating virtual environment..."
source venv/bin/activate
handle_error $? "Failed to activate virtual environment" "Try running 'source venv/bin/activate' manually"
log "SUCCESS" "Virtual environment activated"

# Install wheel and setuptools
log "SYSTEM" "Step 2: Installing dependencies..."
log "SYSTEM" "Installing wheel and setuptools first..."
pip install wheel setuptools --upgrade -v
handle_error $? "Failed to install wheel and setuptools" "Try running with sudo or using --user flag"
log "SUCCESS" "Wheel and setuptools installed"

# Install spaCy
log "SYSTEM" "Installing spaCy and downloading language model..."
pip install spacy --no-build-isolation -v
if [ $? -ne 0 ]; then
    log "ERROR" "==================================================="
    log "ERROR" "Failed to install spaCy."
    log "INFO" "You may need to install build dependencies:"
    log "INFO" "Ubuntu/Debian: sudo apt-get install build-essential python3-dev"
    log "INFO" "Fedora/RHEL/CentOS: sudo dnf install gcc-c++ python3-devel"
    log "INFO" "macOS: xcode-select --install"
    log "INFO" ""
    log "INFO" "After installing the dependencies, run this script again."
    log "ERROR" "==================================================="
    exit 1
else
    log "SUCCESS" "spaCy installed"
fi

# Download spaCy language model
log "SYSTEM" "Downloading spaCy language model..."
python -m spacy download en_core_web_sm -v
handle_error $? "Failed to download spaCy language model" "Try running 'python -m spacy download en_core_web_sm' manually"
log "SUCCESS" "spaCy language model downloaded"

# Install remaining dependencies
log "SYSTEM" "Installing remaining dependencies..."
pip install -r requirements.txt
handle_error $? "Some dependencies may not be installed correctly" "You can try installing them manually if you encounter issues"
log "SUCCESS" "Dependencies installed"

# Export model
log "SYSTEM" "Step 3: Exporting emotion analysis model..."
if [ ! -f "models/emotion_model.onnx" ]; then
    log "SYSTEM" "Exporting model to ONNX format..."
    PYTHONPATH=. python src/main.py --export-model
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to export model"
        log "INFO" "Check if CUDA drivers are properly installed for GPU acceleration"
        log "INFO" "Try running with CPU only: PYTHONPATH=. CUDA_VISIBLE_DEVICES=-1 python src/main.py --export-model"
        exit 1
    fi
    log "SUCCESS" "Model exported successfully"
else
    log "SYSTEM" "Model already exists, skipping export."
fi

# Prepare EZKL environment
log "SYSTEM" "Step 4: Preparing EZKL environment..."
if [ ! -f "ezkl_files/circuit.ezkl" ]; then
    log "SYSTEM" "Setting up EZKL environment..."
    PYTHONPATH=. python src/main.py --prepare-ezkl
    EZKL_EXIT_CODE=$?
    
    if [ $EZKL_EXIT_CODE -ne 0 ]; then
        log "ERROR" "Failed to prepare EZKL environment (exit code $EZKL_EXIT_CODE)"
        log "INFO" "Check if the ONNX model was exported correctly"
        log "INFO" "Verify that ezKL is installed properly: pip show ezkl"
        log "INFO" "Ensure you have sufficient disk space and memory"
        exit 1
    fi
    log "SUCCESS" "EZKL environment prepared successfully"
else
    log "SYSTEM" "EZKL environment already prepared, skipping setup."
fi

# Start web application
log "SYSTEM" "==================================================="
log "SUCCESS" "Setup complete! Starting web application..."
log "SYSTEM" "==================================================="
log "SYSTEM" "The application will be available at http://localhost:5000"
log "SYSTEM" "Press Ctrl+C to stop the application."

# Run the application while still logging its output
log "SYSTEM" "Running web application..."
log "SYSTEM" "APPLICATION: Starting web server (logs below):"

# Use a timeout for proper shutdown handling
{
    # Run with timeout to capture exit code/signals
    (PYTHONPATH=. python run_web_app.py 2>&1) | while read line; do 
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] APP: $line" | tee -a "$LOG_FILE"
    done
} || {
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        # Timeout occurred
        log "SYSTEM" "Application timed out"
    elif [ $exit_code -eq 130 ]; then
        # SIGINT (Ctrl+C)
        log "SYSTEM" "Application stopped by user (Ctrl+C)"
    else
        log "ERROR" "Application terminated with error code: $exit_code"
    fi
}

# This will only execute if the Python app exits normally
log "SYSTEM" "Application terminated"
log "SYSTEM" "See $LOG_FILE for complete setup and application logs."

# Clean up
exec 1>&3
exec 2>&4