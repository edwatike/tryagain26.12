@echo off
cd /d %~dp0..\backend
echo [Backend] Starting...
if not exist venv (
    echo [Backend] Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [Backend] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [Backend] ERROR: Failed to install dependencies
    exit /b 1
)
echo [Backend] Starting API on port 8000...
python run_api.py
if errorlevel 1 (
    echo [Backend] ERROR: Failed to start API
    exit /b 1
)
