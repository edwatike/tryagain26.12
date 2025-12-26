@echo off
chcp 65001 >nul
cd /d %~dp0parser_service

echo ========================================
echo   Starting Parser Service
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH
    echo Please install Python 3.12+ and add it to PATH
    pause
    exit /b 1
)

REM Check if port 9003 is already in use
netstat -ano | findstr ":9003" >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 9003 is already in use
    echo Parser Service may already be running
    echo.
    echo Checking if Parser Service is accessible...
    curl -s http://127.0.0.1:9003/health >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Parser Service is already running and accessible
        echo You can check it at http://127.0.0.1:9003/health
        pause
        exit /b 0
    ) else (
        echo [ERROR] Port 9003 is in use but Parser Service is not accessible
        echo Please stop the process using port 9003 and try again
        pause
        exit /b 1
    )
)

REM Check if Chrome CDP is running
echo [1/5] Checking Chrome CDP...
curl -s http://127.0.0.1:9222/json/version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Chrome CDP is not accessible on port 9222
    echo Parser Service requires Chrome to be running in CDP mode
    echo Please run start-chrome.bat first
    echo.
    echo Continuing anyway (Parser Service will fail to connect to Chrome)...
) else (
    echo [OK] Chrome CDP is accessible
)

REM Create venv if it doesn't exist
echo [2/5] Checking virtual environment...
if not exist venv (
    echo [Parser] Creating venv...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [OK] Virtual environment exists
)

REM Activate venv
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo [4/5] Installing dependencies...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

REM Install Playwright browsers
echo [5/5] Installing Playwright browsers...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install Playwright browsers
    echo This may cause issues when parsing
)

REM Check if Chrome CDP is still accessible before starting
echo.
echo Checking Chrome CDP one more time...
curl -s http://127.0.0.1:9222/json/version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Chrome CDP is not accessible!
    echo Parser Service will not be able to connect to Chrome
    echo Please run start-chrome.bat in another window
    echo.
    timeout /t 5 /nobreak >nul
)

REM Start API
echo.
echo ========================================
echo   Starting Parser Service API
echo ========================================
echo API will be available at http://127.0.0.1:9003
echo Health check: http://127.0.0.1:9003/health
echo.
python run_api.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Parser Service failed to start
    echo Check the error messages above
    pause
    exit /b 1
)
pause
