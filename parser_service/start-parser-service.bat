@echo off
chcp 65001 >nul
cd /d %~dp0

echo ========================================
echo   Starting Parser Service API
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH
    echo Please install Python 3.12+ and add it to PATH
    pause
    exit /b 1
)

REM Create venv if it doesn't exist
echo [1/4] Checking virtual environment
if not exist venv (
    echo [Parser] Creating venv
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [OK] Virtual environment exists
)

REM Activate venv
echo [2/4] Activating virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo [3/4] Installing dependencies
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Install Playwright browsers
echo [4/4] Installing Playwright browsers
python -m playwright install chromium
if errorlevel 1 (
    echo [WARNING] Failed to install Playwright browsers
    echo This may cause issues when parsing
)

REM Start API
echo.
echo ========================================
echo   Parser Service API Starting
echo ========================================
echo API will be available at http://127.0.0.1:9003
echo Health check: http://127.0.0.1:9003/health
echo.
python run_api.py
if errorlevel 1 (
    echo.
    echo [ERROR] Parser Service failed to start
    echo Check the error messages above
    pause
    exit /b 1
)
pause

