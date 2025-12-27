@echo off
chcp 65001 >nul

REM Load Chrome CDP configuration
call "%~dp0scripts\chrome_config.bat"

echo ========================================
echo   B2B Platform - Stopping All Services
echo ========================================
echo.

echo Stopping Chrome processes with CDP...
REM Stop Chrome processes on CDP port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%CHROME_CDP_PORT% ^| findstr LISTENING') do (
    echo   Stopping Chrome process %%a on port %CHROME_CDP_PORT%...
    taskkill /F /PID %%a >nul 2>&1
)
REM Stop Chrome processes with CDP flag
taskkill /F /IM chrome.exe /FI "COMMANDLINE eq *--remote-debugging-port=%CHROME_CDP_PORT%*" >nul 2>&1
REM Stop Chrome processes with debug profile
taskkill /F /IM chrome.exe /FI "COMMANDLINE eq *%CHROME_DEBUG_PROFILE%*" >nul 2>&1

echo Stopping Python processes (Backend, Parser)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Backend*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Parser*" >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

echo Stopping Node processes (Frontend)...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *Frontend*" >nul 2>&1
taskkill /F /IM node.exe /FI "COMMANDLINE eq *next dev*" >nul 2>&1

echo.
echo All services stopped!
echo.
pause

