# Audio Transcription Tool - Setup & Run (PowerShell)

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  Audio Transcription Tool - Setup & Run" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$VENV_DIR = "venv"

# Check if virtual environment exists
if (-not (Test-Path "$VENV_DIR\Scripts\Activate.ps1")) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "      Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "[1/4] Virtual environment already exists, skipping..." -ForegroundColor Gray
}

# Activate virtual environment
Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Yellow
& "$VENV_DIR\Scripts\Activate.ps1"

# Upgrade pip and install dependencies
Write-Host "[3/4] Installing/Upgrading dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -e ".[ui]" --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "      Dependencies installed successfully!" -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host "         Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "!! IMPORTANT !!" -ForegroundColor Red
    Write-Host "Please edit the .env file and add your API keys:" -ForegroundColor Yellow
    Write-Host "  - OPENAI_API_KEY=your-key-here" -ForegroundColor White
    Write-Host "  - ANTHROPIC_API_KEY=your-key-here" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to open .env file for editing"
    notepad .env
}

# Run the server
Write-Host ""
Write-Host "[4/4] Starting the UI server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  Server running at: http://localhost:8000" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

python run_ui.py
