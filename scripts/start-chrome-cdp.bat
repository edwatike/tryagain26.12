@echo off
echo ========================================
echo   Запуск Chrome с CDP для Comet
echo ========================================
echo.

REM Закрываем все процессы Chrome
echo [1/4] Останавливаю существующие процессы Chrome...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 3 /nobreak >nul

REM Путь к Chrome
set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

if not exist "%CHROME_PATH%" (
    echo [ERROR] Chrome не найден: %CHROME_PATH%
    pause
    exit /b 1
)

REM Создаем директорию для профиля
set PROFILE_DIR=C:\chrome-comet-debug
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"

echo [2/4] Запускаю Chrome с CDP на порту 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check

echo [3/4] Ожидаю запуск Chrome (15 секунд)...
timeout /t 15 /nobreak >nul

echo [4/4] Проверка CDP...
echo.

REM Проверяем CDP несколько раз
set CDP_READY=0
for /L %%i in (1,1,5) do (
    curl -s http://127.0.0.1:9222/json >nul 2>&1
    if !errorlevel! equ 0 (
        set CDP_READY=1
        goto :cdp_ready
    )
    echo Попытка %%i/5 - CDP не готов, ожидаю...
    timeout /t 2 /nobreak >nul
)

:cdp_ready
if %CDP_READY% equ 1 (
    echo.
    echo ========================================
    echo   ✅ Chrome CDP ГОТОВ!
    echo ========================================
    echo.
    echo 📍 CDP URL: http://127.0.0.1:9222
    echo 📍 Профиль: %PROFILE_DIR%
    echo.
    echo Теперь можно запускать Comet extraction:
    echo - Через фронтенд: http://localhost:3000
    echo - Через API: POST http://127.0.0.1:8000/comet/extract-batch
    echo.
) else (
    echo.
    echo ========================================
    echo   ❌ CDP НЕ ГОТОВ
    echo ========================================
    echo.
    echo Попробуйте:
    echo 1. Перезапустить скрипт
    echo 2. Проверить что Chrome установлен
    echo 3. Закрыть все окна Chrome вручную и повторить
    echo.
)

pause
