@echo off
chcp 65001 >nul
echo ========================================
echo   INN Agent Demo - Запуск программы
echo ========================================
echo.

REM Get script directory
cd /d %~dp0

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import playwright" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [INFO] Installing Playwright browsers...
    playwright install chromium
    if errorlevel 1 (
        echo [WARNING] Failed to install Playwright browsers, but continuing...
    )
) else (
    echo [OK] Dependencies are installed
)

REM Check if URL is provided
if "%~1"=="" (
    echo [ERROR] URL is required
    echo.
    echo Usage: run.bat ^<URL^> [OPTIONS]
    echo.
    echo Examples:
    echo   run.bat example.com
    echo   run.bat https://www.obi.ru
    echo   run.bat www.obi.ru --model qwen2.5:14b
    echo   run.bat example.com --no-auto-chrome
    echo.
    echo Note: You can specify URL with or without https://
    echo For more options, see: python main.py --help
    pause
    exit /b 1
)

REM Run the program
echo.
echo [INFO] Starting INN search agent...
echo [INFO] URL: %~1
echo.
python main.py %*

REM Capture exit code
set EXIT_CODE=%errorlevel%

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

REM Exit with the same code as the program
exit /b %EXIT_CODE%

