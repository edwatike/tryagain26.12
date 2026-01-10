@echo off
chcp 65001 >nul
cd /d "D:\tryagain"
title Frontend
echo [%time%] [Frontend] Starting...
start-frontend.bat
pause
