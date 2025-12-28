@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Load Chrome CDP configuration
call "%~dp0scripts\chrome_config.bat"

REM Check if PowerShell is available
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is not available. Please install PowerShell.
    pause
    exit /b 1
)

echo ========================================
echo   B2B Platform - Starting All Services
echo   Tabby Terminal Version
echo ========================================
echo.

REM ========================================
REM STEP 0: STOP ALL SERVICES (EXCEPT CHROME CDP IF RUNNING)
REM ========================================
echo [0/6] Stopping all services (except Chrome CDP if running)...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\stop-all-services.ps1"
echo.

REM ========================================
REM STEP 1: CHECK CONFIGURATION
REM ========================================
echo [1/6] Checking configuration...
if not exist "backend\.env" (
    echo [WARNING] backend\.env not found!
    echo Please create backend\.env with your DATABASE_URL
) else (
    echo [OK] Configuration found
)
echo.

REM ========================================
REM STEP 2: START CHROME CDP (IF NOT ALREADY RUNNING)
REM ========================================
echo [2/6] Starting Chrome in CDP mode (if not already running)...
call "%~dp0start-chrome.bat"
REM start-chrome.bat returns 0 if Chrome CDP is already running, which is OK
REM Only exit if there was a real error (exit code 1)
if errorlevel 1 (
    echo [ERROR] Failed to start Chrome CDP
    pause
    exit /b 1
)
echo.

REM ========================================
REM STEP 3: START ALL SERVICES IN TABBY
REM ========================================
echo [3/6] Starting all services in Tabby terminal...
echo.

REM Start PowerShell script that will start all services in single window
REM Remove trailing backslash from path
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
REM Run in debug mode by default (detailed logging)
REM To run in production mode: change "debug" to "production"
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start-all-services-single-window.ps1" -ProjectRoot "%PROJECT_ROOT%" -Mode "debug"

if errorlevel 1 (
    echo [ERROR] Failed to start services in Tabby
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Services started in single window!
echo ========================================
echo.
echo All services are running in one terminal window with:
echo   - Colored logging (errors in red, success in green)
echo   - Real-time log monitoring
echo   - Automatic health checks
echo.
echo Mode: debug (detailed logging)
echo To use production mode (optimized), edit start-all-tabby.bat
echo   and change -Mode "debug" to -Mode "production"
echo.
echo URLs:
echo   Frontend:    http://localhost:3000
echo   Backend API: http://127.0.0.1:8000
echo   Backend Docs: http://127.0.0.1:8000/docs
echo   Parser:      http://127.0.0.1:9003
echo.
pause

