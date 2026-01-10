@echo off
chcp 65001 >nul
cls

REM Переходим в корень проекта (на уровень выше от temp)
cd /d "%~dp0.."

REM Если URL передан как аргумент - используем его, иначе спрашиваем
if "%~1"=="" (
    python temp\comet_browser_opener.py
    if errorlevel 1 (
        pause
    )
) else (
    REM Если передан URL и промпт
    if "%~2"=="" (
        python temp\comet_browser_opener.py "%~1"
    ) else (
        python temp\comet_browser_opener.py "%~1" "%~2"
    )
)

