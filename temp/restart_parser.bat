@echo off
chcp 65001 >nul
echo ========================================
echo   Restarting Parser Service
echo ========================================
echo.

REM Find and kill all processes on port 9003
echo [1/3] Stopping existing Parser Service processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9003 ^| findstr LISTENING') do (
    echo Stopping process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

REM Wait a bit
timeout /t 2 /nobreak >nul

REM Check if port is free
netstat -ano | findstr :9003 | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 9003 is still in use. Trying to force stop...
    timeout /t 2 /nobreak >nul
)

echo [2/3] Starting Parser Service...
cd /d %~dp0..\parser_service
start "Parser Service" cmd /k "python run_api.py"

echo [3/3] Waiting for service to start...
timeout /t 5 /nobreak >nul

REM Check if service is running
curl -s http://127.0.0.1:9003/health >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Parser Service is running!
    echo Health check: http://127.0.0.1:9003/health
) else (
    echo [ERROR] Parser Service failed to start
    echo Check the console window for errors
)

echo.
echo ========================================
pause







