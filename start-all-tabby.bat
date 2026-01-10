@echo off
setlocal

REM One-click start for all services (single window)
set PROJECT_ROOT=%~dp0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\start-all-services-single-window.ps1" -ProjectRoot "%PROJECT_ROOT%" -Mode "debug"

pause
endlocal
