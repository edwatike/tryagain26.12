@echo off
chcp 65001 >nul
 setlocal enabledelayedexpansion

REM Load Chrome CDP configuration
call "%~dp0chrome_config.bat"

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
REM Try multiple times to ensure CDP is really accessible
echo [DEBUG] Checking if Chrome CDP is already accessible...
echo [DEBUG] CDP URL: %CHROME_CDP_VERSION_URL%
set CHROME_CDP_ACCESSIBLE=0
for /L %%i in (1,1,5) do (
    echo [DEBUG] Attempt %%i/5: Checking Chrome CDP...
    for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set CDP_HTTP_CODE=%%c
    if "%CDP_HTTP_CODE%"=="200" (
        echo [DEBUG] Chrome CDP accessible on attempt %%i (HTTP %CDP_HTTP_CODE%)
        set CHROME_CDP_ACCESSIBLE=1
        goto chrome_cdp_check_ok
    ) else (
        echo [DEBUG] Chrome CDP not accessible on attempt %%i (HTTP %CDP_HTTP_CODE%)
    )
    if %%i LSS 5 (
        timeout /t 1 /nobreak >nul
    )
)
:chrome_cdp_check_ok
if "%CHROME_CDP_ACCESSIBLE%"=="1" (
    echo [OK] Chrome CDP is already running and accessible
    echo You can check it at %CHROME_CDP_VERSION_URL%
    echo.
    echo Chrome CDP is ready for use!
    echo Chrome will NOT be restarted - using existing instance
    echo.
    REM Exit with success code (0) - Chrome is already running
    exit /b 0
) else (
    echo [DEBUG] Chrome CDP is NOT accessible after 5 attempts
)

REM Check if port is already in use (but CDP not accessible)
REM This means Chrome might be starting or running without CDP
echo [DEBUG] Checking if port %CHROME_CDP_PORT% is in use...
netstat -ano | findstr ":%CHROME_CDP_PORT%" >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Port %CHROME_CDP_PORT% is already in use
    echo [INFO] Waiting a bit more for Chrome CDP to become accessible...
    REM Wait a bit more and check again (Chrome might still be starting)
    timeout /t 3 /nobreak >nul
    echo [DEBUG] Re-checking Chrome CDP after waiting...
    for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set CDP_HTTP_CODE=%%c
    if "%CDP_HTTP_CODE%"=="200" (
        echo [OK] Chrome CDP became accessible after waiting
        echo Chrome CDP is ready for use!
        exit /b 0
    ) else (
        echo [DEBUG] Chrome CDP still not accessible after waiting (HTTP !CDP_HTTP_CODE!)
    )
    echo [WARNING] Port %CHROME_CDP_PORT% is in use but Chrome CDP is still not accessible
    echo This may mean Chrome is running but without --remote-debugging-port=%CHROME_CDP_PORT%
    echo.
    echo IMPORTANT: Before starting Chrome, checking CDP one more time...
    REM Final check before attempting to start Chrome
    curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Chrome CDP is NOW accessible - will NOT start Chrome
        exit /b 0
    )
    echo Options:
    echo   1. Close Chrome and run this script again
    echo   2. Manually start Chrome with: --remote-debugging-port=%CHROME_CDP_PORT%
    echo   3. Continue anyway (Chrome may start CDP later)
    echo.
    echo Continuing to start Chrome with CDP...
    REM Don't exit - try to start Chrome anyway
) else (
    echo [DEBUG] Port %CHROME_CDP_PORT% is NOT in use
)

REM Final check: Is Chrome CDP accessible NOW?
echo [DEBUG] Final check before starting Chrome...
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set "CDP_HTTP_CODE=%%c"
if "!CDP_HTTP_CODE!"=="200" (
    echo [OK] Chrome CDP is accessible - will NOT start Chrome
    echo Chrome CDP is ready for use!
    exit /b 0
)

REM Start Chrome (visible mode - not headless, so you can pass CAPTCHA if needed)
echo [1/2] Starting Chrome with remote debugging on port %CHROME_CDP_PORT%...
echo NOTE: Chrome will be visible (not headless) so you can pass CAPTCHA manually if needed
echo NOTE: Chrome will use a separate debug profile to avoid conflicts
echo Debug profile: %CHROME_DEBUG_PROFILE%
echo [DEBUG] Chrome path: %CHROME_PATH%
echo [DEBUG] Chrome path exists: 
if exist "%CHROME_PATH%" (
    echo [DEBUG] YES - Chrome executable exists
) else (
    echo [DEBUG] NO - Chrome executable NOT found!
    echo [ERROR] Chrome not found at: %CHROME_PATH%
    pause
    exit /b 1
)
REM Use separate user-data-dir for debug profile to ensure CDP works correctly
REM This prevents conflicts with existing Chrome instances
REM All scripts use the SAME profile to ensure consistency
if not exist "%CHROME_DEBUG_PROFILE%" (
    echo [DEBUG] Creating debug profile directory...
    mkdir "%CHROME_DEBUG_PROFILE%"
) else (
    echo [DEBUG] Debug profile directory already exists
)
echo [DEBUG] Attempting to start Chrome...
echo [DEBUG] Command: start "" "%CHROME_PATH%" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" --disable-gpu --no-sandbox --disable-dev-shm-usage
start "" "%CHROME_PATH%" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" --disable-gpu --no-sandbox --disable-dev-shm-usage
set START_RESULT=%errorlevel%
echo [DEBUG] Start command returned errorlevel: %START_RESULT%
REM Note: start command may return errorlevel even if Chrome starts successfully
REM Check if Chrome process was actually started instead
timeout /t 2 /nobreak >nul
for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set "CDP_HTTP_CODE=%%c"
if "!CDP_HTTP_CODE!"=="200" (
    echo [OK] Chrome started successfully (CDP is now accessible)
    REM Chrome started successfully, even if start returned errorlevel
    goto chrome_started_ok
)
if %START_RESULT% neq 0 (
    echo [WARNING] Start command returned errorlevel %START_RESULT%, but checking if Chrome is running...
    REM Check if Chrome process exists
    tasklist | findstr /i chrome.exe >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Chrome process found - may have started despite errorlevel
        echo [INFO] Waiting for CDP to become accessible...
        REM Wait and check CDP
        timeout /t 3 /nobreak >nul
        for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set "CDP_HTTP_CODE=%%c"
        if "!CDP_HTTP_CODE!"=="200" (
            echo [OK] Chrome started successfully (CDP is now accessible)
            goto chrome_started_ok
        )
    )
    echo [ERROR] Failed to start Chrome or Chrome CDP is not accessible
    echo [ERROR] Please check Chrome manually
    pause
    exit /b 1
)
:chrome_started_ok

REM Wait for Chrome to start and CDP to become available
echo [2/2] Waiting for Chrome to start and CDP to become available...
set CHROME_CDP_READY=0
for /L %%i in (1,1,20) do (
    for /f "delims=" %%c in ('curl -s -o NUL -w "%%{http_code}" %CHROME_CDP_VERSION_URL% 2^>nul') do set CDP_HTTP_CODE=%%c
    if "%CDP_HTTP_CODE%"=="200" (
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

