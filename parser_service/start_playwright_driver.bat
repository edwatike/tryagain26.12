@echo off
chcp 65001 >nul
echo ========================================
echo   Starting Playwright Driver
echo ========================================
echo.
echo This script starts Playwright driver in a separate process
echo with correct event loop policy for Windows.
echo.
echo Keep this window open while using the parser.
echo Press Ctrl+C to stop the driver.
echo.
cd /d %~dp0
python start_playwright_driver.py
pause



















