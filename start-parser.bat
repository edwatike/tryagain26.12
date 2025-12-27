@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM Load Chrome CDP configuration
call "%~dp0scripts\chrome_config.bat"

echo ========================================
echo   B2B Platform - Starting All Services
echo ========================================
echo.

REM ========================================
REM STEP 1: CHECK CHROME CDP
REM ========================================
echo [1/7] Checking Chrome CDP...
set CHROME_CDP_RUNNING=0
curl -s %CHROME_CDP_VERSION_URL% >nul 2>nul
if not errorlevel 1 (
    echo [OK] Chrome CDP is already running and accessible on port %CHROME_CDP_PORT%
    echo [INFO] Chrome CDP will NOT be restarted
    set CHROME_CDP_RUNNING=1
) else (
    echo [INFO] Chrome CDP is not accessible, will be started
    set CHROME_CDP_RUNNING=0
)
echo.

REM ========================================
REM STEP 2: STOP ALL SERVICES (EXCEPT CHROME CDP IF RUNNING)
REM ========================================
echo [2/7] Stopping all services...
echo.

REM Stop Chrome processes on CDP port only if CDP is not accessible
if "!CHROME_CDP_RUNNING!"=="0" (
    echo Stopping Chrome processes on port %CHROME_CDP_PORT%...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%CHROME_CDP_PORT% ^| findstr LISTENING') do (
        echo   Stopping Chrome process %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
    REM Also stop all Chrome processes if CDP is not accessible (they may be running without CDP)
    echo Checking for Chrome processes running without CDP...
    tasklist | findstr /i chrome.exe >nul 2>&1
    if not errorlevel 1 (
        echo   Stopping all Chrome processes to restart with CDP...
        taskkill /F /IM chrome.exe >nul 2>&1
        echo   Waiting for Chrome to close...
        ping 127.0.0.1 -n 5 >nul
        REM Verify Chrome is closed - try multiple times
        set CHROME_CLOSED=0
        for /L %%j in (1,1,5) do (
            tasklist | findstr /i chrome.exe >nul 2>&1
            if errorlevel 1 (
                set CHROME_CLOSED=1
                goto chrome_closed_check
            )
            echo   [WARNING] Some Chrome processes are still running, forcing close... (attempt %%j/5)
            taskkill /F /IM chrome.exe >nul 2>&1
            ping 127.0.0.1 -n 3 >nul
        )
        :chrome_closed_check
        if "!CHROME_CLOSED!"=="1" (
            echo   Chrome processes closed
        ) else (
            echo   [WARNING] Some Chrome processes may still be running
        )
    )
) else (
    echo [SKIP] Chrome CDP is running, will not be stopped
)

REM Stop processes on port 9003 (Parser Service)
echo Stopping Parser Service (port 9003)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9003 ^| findstr LISTENING') do (
    echo   Stopping process %%a on port 9003...
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop processes on port 8000 (Backend)
echo Stopping Backend API (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Stopping process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop processes on port 3000 (Frontend)
echo Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
    echo   Stopping process %%a on port 3000...
    taskkill /F /PID %%a >nul 2>&1
)

REM Stop Python processes by window title
echo Stopping Python processes (Backend, Parser)...
taskkill /F /FI "WINDOWTITLE eq *Backend API*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *Parser Service*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *Parser*" >nul 2>&1

REM Stop Node processes by window title
echo Stopping Node processes (Frontend)...
taskkill /F /FI "WINDOWTITLE eq *Frontend*" >nul 2>&1

REM Stop uvicorn processes
echo Stopping uvicorn processes...
taskkill /F /IM uvicorn.exe >nul 2>&1

REM Wait for processes to stop
echo Waiting for processes to stop...
ping 127.0.0.1 -n 4 >nul

echo [OK] All services stopped
echo.

REM ========================================
REM STEP 3: START CHROME CDP (IF NOT ALREADY RUNNING)
REM ========================================
echo [3/7] Starting Chrome in CDP mode...
if "!CHROME_CDP_RUNNING!"=="1" (
    echo [SKIP] Chrome CDP is already running, skipping startup
    echo OK: Chrome CDP is available on port %CHROME_CDP_PORT%
) else (
    echo NOTE: Chrome will be VISIBLE ^(not headless^) so you can pass CAPTCHA manually if needed
    echo NOTE: Chrome will use a separate debug profile to avoid conflicts
    echo Debug profile: %CHROME_DEBUG_PROFILE%
    REM Ensure Chrome is fully closed before starting
    tasklist | findstr /i chrome.exe >nul 2>&1
    if not errorlevel 1 (
        echo   Ensuring all Chrome processes are closed...
        taskkill /F /IM chrome.exe >nul 2>&1
        ping 127.0.0.1 -n 5 >nul
    )
    REM Start Chrome directly with CDP parameters using unified profile
    if exist "!CHROME_PATH!" (
        echo Starting Chrome with CDP on port %CHROME_CDP_PORT%...
        if not exist "!CHROME_DEBUG_PROFILE!" mkdir "!CHROME_DEBUG_PROFILE!"
        start "" "!CHROME_PATH!" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="!CHROME_DEBUG_PROFILE!" --disable-gpu --no-sandbox --disable-dev-shm-usage
        REM Wait for Chrome to start and CDP to become available
        echo   Waiting for Chrome to start...
        ping 127.0.0.1 -n 3 >nul
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
        if "!CHROME_CDP_READY!"=="0" (
            echo [ERROR] Chrome started but CDP is still not accessible after 20 seconds
            echo [ERROR] Please check Chrome manually or restart it with: start-chrome.bat
            echo [ERROR] CDP URL: %CHROME_CDP_VERSION_URL%
        )
    ) else (
        echo [ERROR] Chrome not found at: !CHROME_PATH!
        echo [ERROR] Please install Google Chrome or update the path in scripts\chrome_config.bat
    )
)
echo.

REM ========================================
REM STEP 4: START PARSER SERVICE
REM ========================================
echo [4/7] Starting Parser Service...
start "Parser Service" cmd /k "%~dp0parser_service\start-parser-service.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Parser Service window opened
echo.

REM ========================================
REM STEP 5: START BACKEND
REM ========================================
echo [5/7] Starting Backend API...
start "Backend API" cmd /k "%~dp0start-backend.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Backend API window opened
echo.

REM ========================================
REM STEP 6: START FRONTEND
REM ========================================
echo [6/7] Starting Frontend...
start "Frontend" cmd /k "%~dp0start-frontend.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Frontend window opened
echo.

REM ========================================
REM STEP 7: VERIFY SERVICES AND TEST PARSING
REM ========================================
echo [7/7] Verifying services and testing parsing...
echo.
echo ========================================
echo   All services are starting!
echo ========================================
echo.
echo Services will open in separate windows.
echo Check the windows for any errors.
echo.
echo URLs:
echo   Frontend:    http://localhost:3000
echo   Backend API: http://127.0.0.1:8000
echo   Backend Docs: http://127.0.0.1:8000/docs
echo   Parser:      http://127.0.0.1:9003
echo.
echo Waiting 30 seconds for services to start...
echo Note: Parser Service may take longer to start (installing dependencies, Playwright browsers)
ping 127.0.0.1 -n 31 >nul

echo.
echo Checking services...
echo.

REM Check Chrome CDP
curl -s http://127.0.0.1:9222/json/version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Chrome CDP not responding on http://127.0.0.1:9222
) else (
    echo [OK] Chrome CDP is running on http://127.0.0.1:9222
)

REM Check Backend
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Backend not responding on http://127.0.0.1:8000
) else (
    echo [OK] Backend is running on http://127.0.0.1:8000
)

REM Check Parser Service (may need more time)
echo Checking Parser Service (this may take a moment)...
set PARSER_READY=0
for /L %%i in (1,1,5) do (
    curl -s http://127.0.0.1:9003/health >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Parser Service is running on http://127.0.0.1:9003
        set PARSER_READY=1
        goto :parser_check_done
    )
    if %%i LSS 5 (
        echo Waiting for Parser Service to start... (attempt %%i/5)
        ping 127.0.0.1 -n 3 >nul
    )
)
:parser_check_done
if "%PARSER_READY%"=="0" (
    echo [WARNING] Parser Service not responding on http://127.0.0.1:9003
    echo [INFO] Check the Parser Service window for errors
    echo [INFO] Parser Service may still be installing dependencies or Playwright browsers
)

REM Check Frontend
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Frontend not responding on http://localhost:3000
) else (
    echo [OK] Frontend is running on http://localhost:3000
)

echo.
echo ========================================
echo   Testing Parsing
echo ========================================
echo.

REM Wait a bit more for services to be fully ready
echo.
if "%PARSER_READY%"=="0" (
    echo [INFO] Parser Service is not ready yet, skipping parsing test
    echo [INFO] Please wait for Parser Service to finish starting, then test manually
) else (
    echo Waiting 3 more seconds for services to be fully ready...
    ping 127.0.0.1 -n 4 >nul
    
    REM Test parsing
    echo Testing parsing with keyword: "test", depth: 1, source: "yandex"
    echo.
    
    REM Test parsing using curl with inline JSON
    curl -X POST http://127.0.0.1:8000/parsing/start -H "Content-Type: application/json" -d "{\"keyword\":\"test\",\"depth\":1,\"source\":\"yandex\"}" -w "\nHTTP Status: %%{http_code}\n" 2>nul
    
    if errorlevel 1 (
        echo.
        echo [WARNING] Parsing test request failed
        echo This may be normal if services are still starting
        echo Try again manually from the frontend at http://localhost:3000/manual-parsing
    ) else (
        echo.
        echo [OK] Parsing test request sent successfully
        echo Check the response above for runId
        echo If you see runId, parsing was started successfully
    )
)

echo.
echo ========================================
echo   Startup complete!
echo ========================================
echo.
echo Press any key to close this window...
pause
