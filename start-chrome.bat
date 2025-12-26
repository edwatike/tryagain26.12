@echo off
chcp 65001 >nul
echo ========================================
echo   Starting Chrome in CDP mode
echo ========================================
echo.
echo NOTE: Chrome will run in VISIBLE mode (not headless)
echo       This allows you to manually pass CAPTCHA if needed
echo.

REM Check if Chrome exists
set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" (
    echo [ERROR] Chrome not found at: %CHROME_PATH%
    echo Please install Google Chrome or update the path in start-chrome.bat
    pause
    exit /b 1
)

REM Check if port 9222 is already in use
netstat -ano | findstr ":9222" >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 9222 is already in use
    echo Chrome CDP may already be running
    echo.
    echo Checking if Chrome CDP is accessible...
    curl -s http://127.0.0.1:9222/json/version >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Chrome CDP is already running and accessible
        echo You can check it at http://127.0.0.1:9222/json/version
        pause
        exit /b 0
    ) else (
        echo [ERROR] Port 9222 is in use but Chrome CDP is not accessible
        echo Please stop the process using port 9222 and try again
        pause
        exit /b 1
    )
)

REM Start Chrome (visible mode - not headless, so you can pass CAPTCHA if needed)
echo [1/2] Starting Chrome with remote debugging on port 9222...
echo NOTE: Chrome will be visible (not headless) so you can pass CAPTCHA manually if needed
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --disable-gpu --no-sandbox --disable-dev-shm-usage
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Chrome
    pause
    exit /b 1
)

REM Wait for Chrome to start
echo [2/2] Waiting for Chrome to start...
timeout /t 3 /nobreak >nul

REM Check if Chrome CDP is accessible
echo Checking Chrome CDP accessibility...
curl -s http://127.0.0.1:9222/json/version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Chrome started successfully in CDP mode
    echo Chrome is available at http://127.0.0.1:9222
    echo You can check it at http://127.0.0.1:9222/json/version
) else (
    echo [WARNING] Chrome started but CDP endpoint is not yet accessible
    echo This may take a few more seconds. Please check manually:
    echo   http://127.0.0.1:9222/json/version
)

echo.
echo ========================================
echo   Chrome CDP startup complete
echo ========================================
pause

