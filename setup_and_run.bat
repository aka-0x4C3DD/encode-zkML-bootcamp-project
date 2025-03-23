@echo off
setlocal EnableDelayedExpansion

REM Create a timestamped log file
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "datestamp=%dt:~0,8%"
set "timestamp=%dt:~8,6%"
set "LOG_FILE=setup_log_%datestamp%_%timestamp%.txt"
echo [%date% %time%] Setup started > %LOG_FILE%
echo [%date% %time%] Creating log file: %LOG_FILE% >> %LOG_FILE%

REM Set PYTHONPATH to current directory for proper module imports
set "PYTHONPATH=."
echo [%date% %time%] Setting PYTHONPATH to current directory >> %LOG_FILE%

REM Define color codes for Windows console
set "RED=Error"
set "YELLOW=Warning"
set "GREEN=Success"
set "BLUE=Info"
set "NC=System"

echo ===================================================
echo Privacy-Preserving Emotion Analysis Setup
echo ===================================================
echo Verbose logs will be saved to %LOG_FILE%

REM Check if tee is available
echo [%date% %time%] Checking for tee command... >> %LOG_FILE%
where tee >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] tee command not found, installing temporary version... >> %LOG_FILE%
    
    REM Create a directory for tools if it doesn't exist
    if not exist tools mkdir tools
    echo [%date% %time%] Created tools directory >> %LOG_FILE%
    
    REM Download tee.exe from GitHub repository (using PowerShell)
    echo [%date% %time%] Downloading tee.exe from GitHub... >> %LOG_FILE%
    echo [%date% %time%] Command: powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/dEajL3kA/tee-win32/releases/download/v1.3/tee-win32.zip' -OutFile 'tools\tee-win32.zip'}" >> %LOG_FILE%
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/dEajL3kA/tee-win32/releases/download/v1.3/tee-win32.zip' -OutFile 'tools\tee-win32.zip'}" >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "%RED%" "Failed to download tee utility"
        call :log "%BLUE%" "Check your internet connection"
    )
    
    REM Extract tee.exe from the archive
    echo [%date% %time%] Extracting tee.exe... >> %LOG_FILE%
    echo [%date% %time%] Command: powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('tools\tee-win32.zip', 'tools')}" >> %LOG_FILE%
    powershell -Command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('tools\tee-win32.zip', 'tools')}" >> %LOG_FILE% 2>&1
    
    REM Copy tee.exe to the current directory for immediate use
    echo [%date% %time%] Copying tee.exe to current directory... >> %LOG_FILE%
    copy tools\tee.exe . >> %LOG_FILE% 2>&1
    
    REM Add the current directory to PATH for this session
    echo [%date% %time%] Adding current directory to PATH... >> %LOG_FILE%
    set "PATH=%CD%;%PATH%"
    
    REM Verify tee is now available
    echo [%date% %time%] Verifying tee installation... >> %LOG_FILE%
    where tee >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "%RED%" "Failed to install tee, using fallback logging method"
        set USE_TEE=0
    ) else (
        call :log "%GREEN%" "tee command is now available"
        set USE_TEE=1
    )
) else (
    call :log "%GREEN%" "tee command found"
    set USE_TEE=1
)

REM Enhanced Log formatter function with categories
:log
setlocal
set "category=%~1"
set "message=%~2"
set "timestamp=%date% %time%"

REM Format the message based on category
if "%category%"=="%RED%" (
    set "formatted_message=[%timestamp%] ERROR: %message%"
) else if "%category%"=="%YELLOW%" (
    set "formatted_message=[%timestamp%] WARNING: %message%"
) else if "%category%"=="%GREEN%" (
    set "formatted_message=[%timestamp%] SUCCESS: %message%"
) else if "%category%"=="%BLUE%" (
    set "formatted_message=[%timestamp%] INFO: %message%"
) else (
    set "formatted_message=[%timestamp%] SYSTEM: %message%"
)

if %USE_TEE%==1 (
    echo %formatted_message% | tee -a %LOG_FILE%
) else (
    echo %formatted_message%
    echo %formatted_message% >> %LOG_FILE%
)
endlocal
goto :eof

REM Enhanced error handler with suggestions
:handle_error
setlocal
set "exit_code=%~1"
set "error_message=%~2"
set "suggestion=%~3"

if %exit_code% neq 0 (
    call :log "%RED%" "%error_message%"
    if not "%suggestion%"=="" (
        call :log "%BLUE%" "%suggestion%"
    )
    endlocal
    exit /b 1
)
endlocal
exit /b 0

REM Check if Python is installed
call :log "%NC%" "Checking for Python installation..."
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%RED%" "Python not found. Please install Python 3.8 or higher."
    call :log "%BLUE%" "Download from https://www.python.org/downloads/"
    pause
    exit /b 1
) else (
    python --version > temp_version.txt
    set /p PYTHON_VERSION=<temp_version.txt
    del temp_version.txt
    call :log "%GREEN%" "Found %PYTHON_VERSION%"
)

call :log "%NC%" ""
call :log "%NC%" "Step 0: Upgrading pip..."
python -m pip install --upgrade pip -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%YELLOW%" "Failed to upgrade pip, but continuing setup."
    call :log "%BLUE%" "You may need to run this script with administrator privileges"
) else (
    call :log "%GREEN%" "Pip upgraded successfully."
)

call :log "%NC%" ""
call :log "%NC%" "Step 1: Creating virtual environment..."
if not exist venv (
    call :log "%NC%" "Creating new virtual environment..."
    python -m venv venv >> %LOG_FILE% 2>&1
    call :handle_error %ERRORLEVEL% "Failed to create virtual environment." "Check if your Python installation includes venv. If not, install it with: pip install virtualenv"
    call :log "%GREEN%" "Virtual environment created successfully."
) else (
    call :log "%NC%" "Virtual environment already exists."
)

call :log "%NC%" "Activating virtual environment..."
call venv\Scripts\activate >> %LOG_FILE% 2>&1
call :handle_error %ERRORLEVEL% "Failed to activate virtual environment." "Try running: venv\Scripts\activate.bat manually"
call :log "%GREEN%" "Virtual environment activated."

call :log "%NC%" ""
call :log "%NC%" "Step 2: Installing dependencies..."
call :log "%NC%" "Installing wheel and setuptools first..."
pip install wheel setuptools --upgrade -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%YELLOW%" "Failed to install wheel and setuptools."
    call :log "%BLUE%" "You may need to run with administrator privileges or use --user flag"
) else (
    call :log "%GREEN%" "Wheel and setuptools installed successfully."
)

call :log "%NC%" ""
call :log "%NC%" "Installing spaCy and downloading language model..."
pip install spacy --no-build-isolation -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%RED%" "==================================================="
    call :log "%RED%" "Failed to install spaCy. You need Microsoft Visual C++ Build Tools."
    call :log "%BLUE%" "Please download and install from:"
    call :log "%BLUE%" "https://visualstudio.microsoft.com/visual-cpp-build-tools/"
    call :log "%BLUE%" ""
    call :log "%BLUE%" "After installing, run this script again."
    call :log "%RED%" "==================================================="
    pause
    exit /b 1
) else (
    call :log "%GREEN%" "SpaCy installed successfully."
)

call :log "%NC%" "Downloading spaCy language model..."
python -m spacy download en_core_web_sm -v >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%YELLOW%" "Failed to download spaCy language model, but continuing setup."
    call :log "%BLUE%" "Try running: python -m spacy download en_core_web_sm manually"
) else (
    call :log "%GREEN%" "SpaCy language model downloaded successfully."
)

call :log "%NC%" ""
call :log "%NC%" "Installing remaining dependencies..."
pip install -r requirements.txt >> %LOG_FILE% 2>&1
if %ERRORLEVEL% neq 0 (
    call :log "%YELLOW%" "Some dependencies may not be installed correctly."
    call :log "%BLUE%" "You can try installing them manually if you encounter issues."
    call :log "%BLUE%" "Check %LOG_FILE% for detailed error messages."
) else (
    call :log "%GREEN%" "All dependencies installed successfully."
)

call :log "%NC%" ""
call :log "%NC%" "Step 3: Exporting emotion analysis model..."
if not exist models\emotion_model.onnx (
    call :log "%NC%" "Exporting model to ONNX format..."
    python -m src.main --export-model >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "%RED%" "Failed to export model."
        call :log "%BLUE%" "Check if GPU drivers are properly installed."
        call :log "%BLUE%" "Try running with CPU only: set CUDA_VISIBLE_DEVICES=-1"
        call :log "%BLUE%" "Check %LOG_FILE% for detailed error messages."
        pause
        exit /b 1
    ) else (
        call :log "%GREEN%" "Model exported successfully."
    )
) else (
    call :log "%NC%" "Model already exists, skipping export."
)

call :log "%NC%" ""
call :log "%NC%" "Step 4: Preparing EZKL environment..."
if not exist ezkl_files\circuit.ezkl (
    call :log "%NC%" "Setting up EZKL environment..."
    python -m src.main --prepare-ezkl >> %LOG_FILE% 2>&1
    if %ERRORLEVEL% neq 0 (
        call :log "%RED%" "Failed to prepare EZKL environment."
        call :log "%BLUE%" "Check if the ONNX model was exported correctly."
        call :log "%BLUE%" "Verify that ezKL is installed properly: pip show ezkl"
        call :log "%BLUE%" "Ensure you have sufficient disk space and memory."
        pause
        exit /b 1
    ) else (
        call :log "%GREEN%" "EZKL environment prepared successfully."
    )
) else (
    call :log "%NC%" "EZKL environment already prepared, skipping setup."
)

call :log "%NC%" ""
call :log "%NC%" "==================================================="
call :log "%GREEN%" "Setup complete! Starting web application..."
call :log "%NC%" "==================================================="
call :log "%NC%" ""
call :log "%NC%" "The application will be available at http://localhost:5000"
call :log "%NC%" "Press Ctrl+C to stop the application."
call :log "%NC%" ""

REM Run application with output captured in log file with better error handling
call :log "%NC%" "Running web application..."
call :log "%NC%" "APPLICATION: Starting web server (logs below):"
call :log "%NC%" ""

REM Run the web app with improved error handling
set "STARTTIME=%time: =0%"
REM Store current error level before running python, to check if terminated abnormally 
set PREVIOUS_ERROR=%ERRORLEVEL%

python run_web_app.py 2>&1 | findstr /V /C:"" | for /F "tokens=*" %%a in ('more') do (
    call :log "APP" "%%a"
)

set APP_EXIT_CODE=%ERRORLEVEL%
set "ENDTIME=%time: =0%"

REM Check if the app exited with an error
if %APP_EXIT_CODE% neq %PREVIOUS_ERROR% (
    call :log "%RED%" "Application terminated with error code: %APP_EXIT_CODE%"
    call :log "%BLUE%" "Check the log file for more details: %LOG_FILE%"
) else (
    call :log "%NC%" "Application terminated successfully"
)

REM Calculate runtime duration
call :calculate_duration "%STARTTIME%" "%ENDTIME%"
call :log "%NC%" "Application runtime: %DURATION%"
call :log "%NC%" "Application terminated. See %LOG_FILE% for setup logs."

pause
exit /b 0

REM Function to calculate time duration
:calculate_duration
setlocal
set "start=%~1"
set "end=%~2"

set "start_h=%start:~0,2%"
set "start_m=%start:~3,2%"
set "start_s=%start:~6,2%"
set "start_ms=%start:~9,2%"
set /a "start_time_in_ms=(((start_h*60)+start_m)*60+start_s)*100+start_ms"

set "end_h=%end:~0,2%"
set "end_m=%end:~3,2%"
set "end_s=%end:~6,2%"
set "end_ms=%end:~9,2%"
set /a "end_time_in_ms=(((end_h*60)+end_m)*60+end_s)*100+end_ms"

set /a "duration_in_ms=end_time_in_ms-start_time_in_ms"
if %duration_in_ms% lss 0 set /a "duration_in_ms+=8640000"

set /a "duration_h=duration_in_ms/360000"
set /a "duration_in_ms%=360000"
set /a "duration_m=duration_in_ms/6000"
set /a "duration_in_ms%=6000"
set /a "duration_s=duration_in_ms/100"
set /a "duration_ms=duration_in_ms%%100"

if %duration_h% lss 10 set "duration_h=0%duration_h%"
if %duration_m% lss 10 set "duration_m=0%duration_m%"
if %duration_s% lss 10 set "duration_s=0%duration_s%"
if %duration_ms% lss 10 set "duration_ms=0%duration_ms%"

endlocal & set "DURATION=%duration_h%:%duration_m%:%duration_s%.%duration_ms%"
goto :eof
