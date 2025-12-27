@echo off
chcp 65001 >nul

REM Load Chrome CDP configuration
call "%~dp0scripts\chrome_config.bat"

echo ========================================
echo   B2B Platform - Starting All Services
echo ========================================
echo.

REM ========================================
REM STEP 0: FORCE STOP ALL SERVICES (EXCEPT CHROME CDP IF RUNNING)
REM ========================================
echo [0/6] Force stopping all services...
echo.

REM Check if Chrome CDP is already running and accessible
echo Checking if Chrome CDP is already running...
set CHROME_CDP_RUNNING=0
curl -s %CHROME_CDP_VERSION_URL% >nul 2>nul
if not errorlevel 1 (
    echo [OK] Chrome CDP is already running and accessible on port %CHROME_CDP_PORT%
    echo [INFO] Chrome CDP will NOT be restarted
    set CHROME_CDP_RUNNING=1
) else (
    echo [INFO] Chrome CDP is not accessible, will be started
    REM Stop Chrome processes on CDP port only if CDP is not accessible
    echo Stopping Chrome processes on port %CHROME_CDP_PORT%...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%CHROME_CDP_PORT% ^| findstr LISTENING') do (
        echo   Stopping Chrome process %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
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

REM Verify ports are free
echo Verifying ports are free...
netstat -ano | findstr ":9003" | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 9003 is still in use!
) else (
    echo [OK] Port 9003 is free
)

netstat -ano | findstr ":8000" | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 8000 is still in use!
) else (
    echo [OK] Port 8000 is free
)

netstat -ano | findstr ":3000" | findstr LISTENING >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] Port 3000 is still in use!
) else (
    echo [OK] Port 3000 is free
)

echo [OK] All services stopped
echo.

REM ========================================
REM STEP 1: CHECK CONFIGURATION
REM ========================================
echo [1/6] Checking configuration...
if not exist "backend\.env" (
    echo WARNING: backend\.env not found!
    echo Please create backend\.env with your DATABASE_URL
    echo Example: DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
    echo.
    ping 127.0.0.1 -n 4 >nul
) else (
    echo OK: Configuration found
)
echo.

REM ========================================
REM STEP 2: START CHROME CDP (IF NOT ALREADY RUNNING)
REM ========================================
echo [2/6] Starting Chrome in CDP mode...
if "%CHROME_CDP_RUNNING%"=="1" (
    echo [SKIP] Chrome CDP is already running, skipping startup
    echo OK: Chrome CDP is available on port %CHROME_CDP_PORT%
) else (
    echo NOTE: Chrome will be VISIBLE ^(not headless^) so you can pass CAPTCHA manually if needed
    echo NOTE: Chrome will use a separate debug profile to avoid conflicts
    echo Debug profile: %CHROME_DEBUG_PROFILE%
    REM Use separate user-data-dir for debug profile to ensure CDP works correctly
    REM All scripts use the SAME profile to ensure consistency
    if not exist "%CHROME_DEBUG_PROFILE%" mkdir "%CHROME_DEBUG_PROFILE%"
    if not exist "%CHROME_PATH%" (
        echo [ERROR] Chrome not found at: %CHROME_PATH%
        echo [ERROR] Please install Google Chrome or update the path in scripts\chrome_config.bat
    ) else (
        start "" "%CHROME_PATH%" --remote-debugging-port=%CHROME_CDP_PORT% --user-data-dir="%CHROME_DEBUG_PROFILE%" --disable-gpu --no-sandbox --disable-dev-shm-usage
        echo   Waiting for Chrome to start...
        ping 127.0.0.1 -n 3 >nul
        set CHROME_CDP_READY=0
        for /L %%i in (1,1,15) do (
            curl -s %CHROME_CDP_VERSION_URL% >nul 2>&1
            if not errorlevel 1 (
                echo [OK] Chrome CDP is accessible on port %CHROME_CDP_PORT%
                set CHROME_CDP_READY=1
                goto chrome_cdp_check_done
            )
            if %%i LSS 15 (
                echo   Waiting for Chrome CDP... (attempt %%i/15)
                timeout /t 1 /nobreak >nul
            )
        )
        :chrome_cdp_check_done
        if "%CHROME_CDP_READY%"=="0" (
            echo [WARNING] Chrome started but CDP is not yet accessible
            echo [WARNING] This may take a few more seconds. Please check manually:
            echo [WARNING] CDP URL: %CHROME_CDP_VERSION_URL%
        ) else (
            echo OK: Chrome started on port %CHROME_CDP_PORT%
        )
    )
)
echo.

REM ========================================
REM STEP 3: START PARSER SERVICE
REM ========================================
echo [3/6] Starting Parser Service...
start "Parser Service" cmd /k "%~dp0start-parser.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Parser Service window opened
echo.

REM ========================================
REM STEP 4: START BACKEND
REM ========================================
echo [4/6] Starting Backend API...
start "Backend API" cmd /k "%~dp0start-backend.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Backend API window opened
echo.

REM ========================================
REM STEP 5: START FRONTEND
REM ========================================
echo [5/6] Starting Frontend...
start "Frontend" cmd /k "%~dp0start-frontend.bat"
ping 127.0.0.1 -n 3 >nul
echo OK: Frontend window opened
echo.

REM ========================================
REM STEP 6: VERIFY SERVICES
REM ========================================
echo [6/6] Verifying services...
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
ping 127.0.0.1 -n 31 >nul

echo.
echo Checking services...
echo.

REM Check Backend with retries
set BACKEND_READY=0
for /L %%i in (1,1,5) do (
    curl -s http://127.0.0.1:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Backend is running on http://127.0.0.1:8000
        set BACKEND_READY=1
        goto backend_check_done
    )
    if %%i LSS 5 (
        echo   Waiting for Backend... (attempt %%i/5)
        timeout /t 2 /nobreak >nul
    )
)
:backend_check_done
if "%BACKEND_READY%"=="0" (
    echo [FAIL] Backend not responding on http://127.0.0.1:8000
    echo [INFO] Check the Backend window for errors
)

REM Check Parser Service with retries (needs more time to start)
set PARSER_READY=0
for /L %%i in (1,1,10) do (
    curl -s http://127.0.0.1:9003/health >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Parser Service is running on http://127.0.0.1:9003
        set PARSER_READY=1
        goto parser_check_done
    )
    if %%i LSS 10 (
        echo   Waiting for Parser Service... (attempt %%i/10)
        timeout /t 3 /nobreak >nul
    )
)
:parser_check_done
if "%PARSER_READY%"=="0" (
    echo [FAIL] Parser Service not responding on http://127.0.0.1:9003
    echo [INFO] Check the Parser Service window for errors
    echo [INFO] Parser Service may need more time to start (installing dependencies, etc.)
    echo [INFO] You can check manually: curl http://127.0.0.1:9003/health
)

REM Check Frontend with retries
set FRONTEND_READY=0
for /L %%i in (1,1,5) do (
    curl -s http://localhost:3000 >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Frontend is running on http://localhost:3000
        set FRONTEND_READY=1
        goto frontend_check_done
    )
    if %%i LSS 5 (
        echo   Waiting for Frontend... (attempt %%i/5)
        timeout /t 2 /nobreak >nul
    )
)
:frontend_check_done
if "%FRONTEND_READY%"=="0" (
    echo [FAIL] Frontend not responding on http://localhost:3000
    echo [INFO] Check the Frontend window for errors
)

echo.
echo ========================================
echo   Startup complete!
echo ========================================
echo.
echo Press any key to close this window...
pause
