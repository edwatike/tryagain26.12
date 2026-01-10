@echo off
chcp 65001 >nul
title Агент поиска ИНН
cls

echo ========================================
echo   Агент поиска ИНН
echo ========================================
echo.

set /p DOMAIN="Введите домен (например: mc.ru): "

if "%DOMAIN%"=="" (
    echo.
    echo [ОШИБКА] Домен не указан!
    pause
    exit /b 1
)

echo.
echo Запуск для: %DOMAIN%
echo.

cd /d "%~dp0"

REM Запуск агента
python temp\run_improved_agent.py "%DOMAIN%"

echo.
pause
