@echo off
chcp 65001 >nul

REM Load Chrome CDP configuration
call "%~dp0scripts\chrome_config.bat"

echo ========================================
echo   Starting Chrome in CDP mode
echo ========================================
echo.
echo NOTE: Chrome will run in VISIBLE mode (not headless)
echo       This allows you to manually pass CAPTCHA if needed
echo.
echo Using debug profile: %CHROME_DEBUG_PROFILE%
echo.

REM Check if Chrome exists
if not exist "%CHROME_PATH%" (
    echo [ERROR] Chrome not found at: %CHROME_PATH%
    echo Please install Google Chrome or update the path in scripts\chrome_config.bat
    pause
    exit /b 1
)

REM Check if Chrome CDP is already accessible
curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Chrome CDP is already running and accessible
    echo You can check it at %CHROME_CDP_VERSION_URL%
    echo.
    echo Chrome CDP is ready for use!
    pause
    exit /b 0
)

REM Check if port is already in use (but CDP not accessible)
netstat -ano | findstr ":%CHROME_CDP_PORT%" >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port %CHROME_CDP_PORT% is already in use but Chrome CDP is not accessible
    echo This may mean Chrome is running but without --remote-debugging-port=%CHROME_CDP_PORT%
    echo.
    echo Please:
    echo   1. Close all Chrome windows
    echo   2. Run this script again
    echo   3. Or manually start Chrome with: --remote-debugging-port=%CHROME_CDP_PORT%
    echo.
    pause
    exit /b 1
)

REM Start Chrome (visible mode - not headless, so you can pass CAPTCHA if needed)
echo [1/2] Starting Chrome with remote debugging on port %CHROME_CDP_PORT%...
echo NOTE: Chrome will be visible (not headless) so you can pass CAPTCHA manually if needed
echo NOTE: Chrome will use a separate debug profile to avoid conflicts
echo Debug profile: %CHROME_DEBUG_PROFILE%
REM Use separate user-data-dir for debug profile to ensure CDP works correctly
REM This prevents conflicts with existing Chrome instances
REM All scripts use the SAME profile to ensure consistency
if not exist "%CHROME_DEBUG_PROFILE%" mkdir "%CHROME_DEBUG_PROFILE%"
start "" "%CHROME_PATH%" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" --disable-gpu --no-sandbox --disable-dev-shm-usage
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Chrome
    pause
    exit /b 1
)

REM Wait for Chrome to start and CDP to become available
echo [2/2] Waiting for Chrome to start and CDP to become available...
set CHROME_CDP_READY=0
for /L %%i in (1,1,20) do (
    curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Chrome CDP is accessible on port %CHROME_CDP_PORT%
        set CHROME_CDP_READY=1
        goto chrome_cdp_check_done
    )
    if %%i LSS 20 (
        echo   Waiting for Chrome CDP... (attempt %%i/20)
        timeout /t 1 /nobreak >nul
    )
)
:chrome_cdp_check_done
if "%CHROME_CDP_READY%"=="0" (
    echo [ERROR] Chrome started but CDP is still not accessible after 20 seconds
    echo [ERROR] Please check Chrome manually or restart it
    echo [ERROR] CDP URL: %CHROME_CDP_VERSION_URL%
) else (
    echo [OK] Chrome started successfully in CDP mode
    echo Chrome is available at %CHROME_CDP_URL%
    echo You can check it at %CHROME_CDP_VERSION_URL%
)

echo.
echo ========================================
echo   Chrome CDP startup complete
echo ========================================
pause

