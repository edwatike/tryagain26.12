@echo off
chcp 65001 >nul
cls

echo ========================================
echo   Агент поиска ИНН - Быстрый запуск
echo ========================================
echo.

REM Проверка, что Chrome запущен
echo [1/3] Проверка Chrome...
curl -s http://127.0.0.1:9222/json/version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Chrome не запущен. Запускаю Chrome...
    call scripts\start-chrome.bat
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] Chrome уже запущен
)

echo.
echo [2/3] Введите домен для поиска ИНН
echo.
set /p DOMAIN="Домен (например: mc.ru или obi.ru): "

REM Нормализация домена (добавляем https:// если нет)
echo %DOMAIN% | findstr /i "http" >nul
if errorlevel 1 (
    set START_URL=https://%DOMAIN%
) else (
    set START_URL=%DOMAIN%
)

echo.
echo [3/3] Запуск агента...
echo.
echo Домен: %DOMAIN%
echo URL: %START_URL%
echo.
echo ========================================
echo.

REM Запуск Python скрипта
python temp\run_improved_agent.py %DOMAIN% %START_URL%

echo.
echo ========================================
echo   Работа завершена
echo ========================================
pause


