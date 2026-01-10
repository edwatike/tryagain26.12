@echo off
REM ========================================
REM Chrome CDP Configuration
REM This file defines common variables for Chrome CDP setup
REM Used by all scripts that need to start Chrome in CDP mode
REM ========================================

REM Chrome executable path
set "COMET_PATH=%LOCALAPPDATA%\Perplexity\Comet\Application\comet.exe"
if exist "%COMET_PATH%" (
    set "CHROME_PATH=%COMET_PATH%"
) else (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
)

REM Chrome CDP port
set "CHROME_CDP_PORT=9222"

REM Chrome CDP URL
set "CHROME_CDP_URL=http://127.0.0.1:%CHROME_CDP_PORT%"

REM Chrome debug profile path (absolute path to ensure consistency)
REM This ensures all scripts use the SAME profile for Chrome CDP
set "CHROME_DEBUG_PROFILE=%~dp0..\temp\chrome_debug_profile"

REM Chrome CDP version endpoint
set "CHROME_CDP_VERSION_URL=%CHROME_CDP_URL%/json/version"

















