@echo off
echo ===================================================
echo Privacy-Preserving Sentiment Analysis Setup
echo ===================================================

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo.
echo Step 0: Upgrading pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo Warning: Failed to upgrade pip, but continuing setup.
)

echo.
echo Step 1: Creating virtual environment...
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)
call venv\Scripts\activate

echo.
echo Step 2: Installing dependencies...
echo Installing wheel and setuptools first...
pip install wheel setuptools --upgrade

echo.
echo Installing spaCy and downloading language model...
pip install spacy --no-build-isolation
if %ERRORLEVEL% neq 0 (
    echo.
    echo ===================================================
    echo ERROR: Failed to install spaCy. You need Microsoft Visual C++ Build Tools.
    echo Please download and install from:
    echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    echo After installing, run this script again.
    echo ===================================================
    pause
    exit /b 1
)

echo Downloading spaCy language model...
python -m spacy download en_core_web_sm
if %ERRORLEVEL% neq 0 (
    echo Warning: Failed to download spaCy language model, but continuing setup.
)

echo.
echo Installing remaining dependencies...
pip install -r requirements.txt --no-deps
if %ERRORLEVEL% neq 0 (
    echo Warning: Some dependencies may not be installed correctly.
    echo You can try installing them manually if you encounter issues.
)

echo.
echo Step 3: Exporting sentiment analysis model...
if not exist models\emotion_model.onnx (
    echo Exporting model to ONNX format...
    python src\main.py --export-model
    if %ERRORLEVEL% neq 0 (
        echo Failed to export model.
        pause
        exit /b 1
    )
) else (
    echo Model already exists, skipping export.
)

echo.
echo Step 4: Preparing EZKL environment...
if not exist ezkl_files\circuit.ezkl (
    echo Setting up EZKL environment...
    python src\main.py --prepare-ezkl
    if %ERRORLEVEL% neq 0 (
        echo Failed to prepare EZKL environment.
        pause
        exit /b 1
    )
) else (
    echo EZKL environment already prepared, skipping setup.
)

echo.
echo ===================================================
echo Setup complete! Starting web application...
echo ===================================================
echo.
echo The application will be available at http://localhost:5000
echo Press Ctrl+C to stop the application.
echo.
python run_web_app.py

pause
