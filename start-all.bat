@echo off
chcp 65001 >nul
echo ========================================
echo   B2B Platform - Starting All Services
echo ========================================
echo.

REM Check if .env file exists
echo [1/5] Checking configuration...
if not exist "backend\.env" (
    echo WARNING: backend\.env not found!
    echo Please create backend\.env with your DATABASE_URL
    echo Example: DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
    echo.
    timeout /t 3 /nobreak >nul
) else (
    echo OK: Configuration found
)
echo.

REM Start Chrome CDP (visible mode - not headless, so you can pass CAPTCHA if needed)
echo [2/5] Starting Chrome in CDP mode...
echo NOTE: Chrome will be VISIBLE (not headless) so you can pass CAPTCHA manually if needed
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --disable-gpu --no-sandbox --disable-dev-shm-usage
timeout /t 3 /nobreak >nul
echo OK: Chrome started on port 9222
echo.

REM Start Parser Service
echo [3/5] Starting Parser Service...
start "Parser Service" cmd /k "%~dp0start-parser.bat"
timeout /t 2 /nobreak >nul
echo OK: Parser Service window opened
echo.

REM Start Backend
echo [4/5] Starting Backend API...
start "Backend API" cmd /k "%~dp0start-backend.bat"
timeout /t 2 /nobreak >nul
echo OK: Backend API window opened
echo.

REM Start Frontend
echo [5/5] Starting Frontend...
start "Frontend" cmd /k "%~dp0start-frontend.bat"
timeout /t 2 /nobreak >nul
echo OK: Frontend window opened
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
echo Waiting 20 seconds to check services...
timeout /t 20 /nobreak >nul

echo.
echo Checking services...
curl -s http://127.0.0.1:8000/health >nul 2>&1 && echo [OK] Backend is running || echo [FAIL] Backend not responding
curl -s http://127.0.0.1:9003/health >nul 2>&1 && echo [OK] Parser is running || echo [FAIL] Parser not responding
curl -s http://localhost:3000 >nul 2>&1 && echo [OK] Frontend is running || echo [FAIL] Frontend not responding

echo.
echo Press any key to close this window...
pause
