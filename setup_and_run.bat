@echo off
setlocal EnableDelayedExpansion

REM Create a log file
set LOG_FILE=setup_log.txt
echo Setup started at %date% %time% > %LOG_FILE%

echo ===================================================
echo Privacy-Preserving Sentiment Analysis Setup
echo ===================================================
echo Verbose logs will be saved to %LOG_FILE%

REM Check if tee is available
echo Checking for tee command...
echo Checking for tee command... >> %LOG_FILE%
where tee >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo tee command not found, installing temporary version...
    echo tee command not found, installing temporary version... >> %LOG_FILE%
    
    REM Create a directory for tools if it doesn't exist
    if not exist tools mkdir tools
    
    REM Download tee.exe from GitHub repository (using PowerShell)
    echo Downloading tee.exe from GitHub... >> %LOG_FILE%
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/dEajL3kA/tee-win32/releases/download/v1.3/tee-win32.zip' -OutFile 'tools\tee-win32.zip'}" >> %LOG_FILE% 2>&1
    
    REM Extract tee.exe from the archive
    echo Extracting tee.exe... >> %LOG_FILE%
    powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('tools\tee-win32.zip', 'tools')}" >> %LOG_FILE% 2>&1
    
    REM Copy tee.exe to the current directory for immediate use
    copy tools\tee.exe . >> %LOG_FILE% 2>&1
    
    REM Add the current directory to PATH for this session
    set "PATH=%CD%;%PATH%"
    
    REM Verify tee is now available
    where tee >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Failed to install tee, using fallback logging method. >> %LOG_FILE%
        echo Failed to install tee, using fallback logging method.
        set USE_TEE=0
    ) else (
        echo tee command is now available. >> %LOG_FILE%
        echo tee command is now available.
        set USE_TEE=1
    )
) else (
    echo tee command found. >> %LOG_FILE%
    echo tee command found.
    set USE_TEE=1
)

REM Function to log messages with or without tee
:log
if %USE_TEE%==1 (
    echo %~1 | tee -a %LOG_FILE%
) else (
    echo %~1
    echo %~1 >> %LOG_FILE%
)
goto :eof

REM Check if Python is installed
call :log "Checking for Python installation..."
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "ERROR: Python not found. Please install Python 3.8 or higher."
    pause
    exit /b 1
) else (
    python --version >> %LOG_FILE%
    call :log "Python found successfully."
)

call :log ""
call :log "Step 0: Upgrading pip..."
python -m pip install --upgrade pip -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "WARNING: Failed to upgrade pip, but continuing setup."
) else (
    call :log "Pip upgraded successfully."
)

call :log ""
call :log "Step 1: Creating virtual environment..."
if not exist venv (
    call :log "Creating new virtual environment..."
    python -m venv venv >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "ERROR: Failed to create virtual environment."
        pause
        exit /b 1
    ) else (
        call :log "Virtual environment created successfully."
    )
) else (
    call :log "Virtual environment already exists."
)

call :log "Activating virtual environment..."
call venv\Scripts\activate >> %LOG_FILE% 2>&1
call :log "Virtual environment activated."

call :log ""
call :log "Step 2: Installing dependencies..."
call :log "Installing wheel and setuptools first..."
pip install wheel setuptools --upgrade -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "WARNING: Failed to install wheel and setuptools."
) else (
    call :log "Wheel and setuptools installed successfully."
)

call :log ""
call :log "Installing spaCy and downloading language model..."
pip install spacy --no-build-isolation -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log ""
    call :log "==================================================="
    call :log "ERROR: Failed to install spaCy. You need Microsoft Visual C++ Build Tools."
    call :log "Please download and install from:"
    call :log "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    call :log ""
    call :log "After installing, run this script again."
    call :log "==================================================="
    pause
    exit /b 1
) else (
    call :log "SpaCy installed successfully."
)

call :log "Downloading spaCy language model..."
python -m spacy download en_core_web_sm -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "WARNING: Failed to download spaCy language model, but continuing setup."
) else (
    call :log "SpaCy language model downloaded successfully."
)

call :log ""
call :log "Installing remaining dependencies..."
pip install -r requirements.txt --no-deps -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "WARNING: Some dependencies may not be installed correctly."
    call :log "You can try installing them manually if you encounter issues."
) else (
    call :log "All dependencies installed successfully."
)

call :log ""
call :log "Step 3: Exporting emotion analysis model..."
if not exist models\emotion_model.onnx (
    call :log "Exporting model to ONNX format..."
    python src\main.py --export-model >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "Failed to export model."
        pause
        exit /b 1
    ) else (
        call :log "Model exported successfully."
    )
) else (
    call :log "Model already exists, skipping export."
)

call :log ""
call :log "Step 4: Preparing EZKL environment..."
if not exist ezkl_files\circuit.ezkl (
    call :log "Setting up EZKL environment..."
    python src\main.py --prepare-ezkl >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "Failed to prepare EZKL environment."
        pause
        exit /b 1
    ) else (
        call :log "EZKL environment prepared successfully."
    )
) else (
    call :log "EZKL environment already prepared, skipping setup."
)

call :log ""
call :log "==================================================="
call :log "Setup complete! Starting web application..."
call :log "==================================================="
call :log ""
call :log "The application will be available at http://localhost:5000"
call :log "Press Ctrl+C to stop the application."
call :log ""

REM Run application - output will go to console only, not log file
call :log "Running application..."
call :log "Application logs will appear below (not saved to log file):"
call :log ""
python run_web_app.py

call :log ""
call :log "Application terminated. See %LOG_FILE% for setup logs."
pause
