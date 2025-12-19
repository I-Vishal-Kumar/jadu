@echo off
echo.
echo ===============================================
echo   Audio Transcription Tool - Setup & Run
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Set virtual environment directory
set VENV_DIR=venv

:: Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [1/4] Creating virtual environment...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo       Virtual environment created successfully!
) else (
    echo [1/4] Virtual environment already exists, skipping...
)

:: Activate virtual environment
echo [2/4] Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

:: Upgrade pip
echo [3/4] Installing/Upgrading dependencies...
python -m pip install --upgrade pip --quiet

:: Install the package with UI dependencies
pip install -e ".[ui]" --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo       Dependencies installed successfully!

:: Check if .env exists
if not exist ".env" (
    echo.
    echo [WARNING] .env file not found!
    echo          Copying from .env.example...
    copy .env.example .env >nul
    echo.
    echo !! IMPORTANT !!
    echo Please edit the .env file and add your API keys:
    echo   - OPENAI_API_KEY=your-key-here
    echo   - ANTHROPIC_API_KEY=your-key-here
    echo.
    echo Press any key to open .env file for editing...
    pause >nul
    notepad .env
)

:: Run the server
echo.
echo [4/4] Starting the UI server...
echo.
echo ===============================================
echo   Server running at: http://localhost:8000
echo   Press Ctrl+C to stop
echo ===============================================
echo.

python run_ui.py
