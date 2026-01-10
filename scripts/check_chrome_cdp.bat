@echo off
chcp 65001 >nul

REM Load Chrome CDP configuration
call "%~dp0chrome_config.bat"
if errorlevel 1 (
    echo [ERROR] Failed to load Chrome CDP configuration
    echo [ERROR] Make sure scripts\chrome_config.bat exists
    pause
    exit /b 1
)

echo ========================================
echo   Chrome CDP Diagnostic Script
echo ========================================
echo.

REM Check if Chrome path exists
echo [1/5] Checking Chrome installation...
if exist "%CHROME_PATH%" (
    echo [OK] Chrome found at: %CHROME_PATH%
) else (
    echo [ERROR] Chrome not found at: %CHROME_PATH%
    echo [ERROR] Please install Google Chrome or update the path in scripts\chrome_config.bat
    echo.
    pause
    exit /b 1
)
echo.

REM Check if debug profile directory exists
echo [2/5] Checking debug profile directory...
if exist "%CHROME_DEBUG_PROFILE%" (
    echo [OK] Debug profile directory exists: %CHROME_DEBUG_PROFILE%
) else (
    echo [INFO] Debug profile directory does not exist: %CHROME_DEBUG_PROFILE%
    echo [INFO] It will be created automatically when Chrome starts
)
echo.

REM Check if port is in use
echo [3/5] Checking port %CHROME_CDP_PORT%...
netstat -ano | findstr ":%CHROME_CDP_PORT%" | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Port %CHROME_CDP_PORT% is in use (Chrome may be running)
    netstat -ano | findstr ":%CHROME_CDP_PORT%" | findstr LISTENING
) else (
    echo [WARNING] Port %CHROME_CDP_PORT% is not in use
    echo [WARNING] Chrome CDP is not running
)
echo.

REM Check Chrome CDP accessibility
echo [4/5] Checking Chrome CDP accessibility...
curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Chrome CDP is accessible!
    echo.
    echo Getting Chrome CDP information...
    curl -s %CHROME_CDP_VERSION_URL% | python -m json.tool 2>nul
    if %errorlevel% neq 0 (
        echo [INFO] JSON parsing failed, showing raw response:
        curl -s %CHROME_CDP_VERSION_URL%
    )
    echo.
    
    REM Check if Chrome is headless
    for /f "tokens=*" %%i in ('curl -s %CHROME_CDP_VERSION_URL% ^| python -c "import sys, json; data=json.load(sys.stdin); print(data.get('User-Agent', ''))" 2^>nul') do set USER_AGENT=%%i
    echo %USER_AGENT% | findstr /i "HeadlessChrome" >nul 2>&1
    if %errorlevel% == 0 (
        echo [WARNING] Chrome is running in HEADLESS mode
        echo [WARNING] This may cause issues with CAPTCHA solving
    ) else (
        echo [OK] Chrome is running in VISIBLE mode
        echo [OK] CAPTCHA solving should work correctly
    )
) else (
    echo [ERROR] Chrome CDP is NOT accessible
    echo [ERROR] URL: %CHROME_CDP_VERSION_URL%
    echo.
    echo Possible causes:
    echo   1. Chrome is not running
    echo   2. Chrome is running without --remote-debugging-port=%CHROME_CDP_PORT%
    echo   3. Chrome is using a different profile
    echo   4. Port %CHROME_CDP_PORT% is blocked by firewall
    echo.
    echo Solution:
    echo   1. Run scripts\start-chrome.bat to start Chrome with CDP
    echo   2. Or run start-all.bat to start all services
)
echo.

REM Check Chrome processes
echo [5/5] Checking Chrome processes...
tasklist | findstr /i chrome.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Chrome processes found:
    tasklist | findstr /i chrome.exe
    echo.
    echo Checking Chrome command line arguments...
    wmic process where "name='chrome.exe'" get processid,commandline | findstr /i "remote-debugging-port" >nul 2>&1
    if %errorlevel% == 0 (
        echo [OK] Found Chrome processes with CDP:
        wmic process where "name='chrome.exe'" get processid,commandline | findstr /i "remote-debugging-port"
    ) else (
        echo [WARNING] Chrome processes found but none with --remote-debugging-port
        echo [WARNING] Chrome may be running without CDP
    )
    echo.
    wmic process where "name='chrome.exe'" get processid,commandline | findstr /i "user-data-dir" >nul 2>&1
    if %errorlevel% == 0 (
        echo [INFO] Chrome processes with user-data-dir:
        wmic process where "name='chrome.exe'" get processid,commandline | findstr /i "user-data-dir"
    )
) else (
    echo [INFO] No Chrome processes found
    echo [INFO] Chrome is not running
)
echo.

echo ========================================
echo   Diagnostic complete
echo ========================================
echo.
echo For more information, check:
echo   - Chrome CDP URL: %CHROME_CDP_VERSION_URL%
echo   - Debug profile: %CHROME_DEBUG_PROFILE%
echo   - Configuration: scripts\chrome_config.bat
echo.
pause

