@echo off
chcp 65001 >nul

call "%~dp0chrome_config.bat"

echo Starting Chrome CDP on port %CHROME_CDP_PORT%...

REM Stop any existing Chrome on this port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%CHROME_CDP_PORT%"') do (
    echo Stopping process %%a on port %CHROME_CDP_PORT%
    taskkill /F /PID %%a >nul 2>&1
)

REM Start Chrome
start "" "%CHROME_PATH%" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" --disable-gpu --no-sandbox --disable-dev-shm-usage

REM Wait for CDP to be ready
echo Waiting for CDP to become ready...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
if %errorlevel% equ 0 (
    echo Chrome CDP is ready at %CHROME_CDP_VERSION_URL%
    exit /b 0
)
goto wait_loop
