@echo off
chcp 65001 >nul
cd /d "D:\tryagain"
title Parser Service
echo [%time%] [Parser Service] Starting...
parser_service\start-parser-service.bat
pause
