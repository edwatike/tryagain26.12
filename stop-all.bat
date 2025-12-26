@echo off
echo ========================================
echo   B2B Platform - Stopping All Services
echo ========================================
echo.

echo Stopping Chrome processes...
taskkill /F /IM chrome.exe /FI "WINDOWTITLE eq *9222*" >nul 2>&1
taskkill /F /IM chrome.exe /FI "COMMANDLINE eq *--remote-debugging-port=9222*" >nul 2>&1

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

