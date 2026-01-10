@echo off
chcp 65001 >nul
cd /d "D:\tryagain"
title Backend
echo [%time%] [Backend] Starting...
start-backend.bat
pause
