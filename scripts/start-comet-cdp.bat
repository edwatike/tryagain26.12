@echo off
echo ========================================
echo   Запуск Comet Browser с CDP
echo ========================================
echo.

REM Закрываем все процессы Comet
echo [1/3] Останавливаю существующие процессы Comet...
taskkill /F /IM comet.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Путь к Comet
set COMET_PATH=C:\Users\admin\AppData\Local\Perplexity\Comet\Application\comet.exe

if not exist "%COMET_PATH%" (
    echo [ERROR] Comet не найден: %COMET_PATH%
    echo Установите Comet browser от Perplexity
    pause
    exit /b 1
)

echo [2/3] Запускаю Comet с CDP на порту 9222...
start "" "%COMET_PATH%" --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1

echo [3/3] Ожидаю запуск CDP (10 секунд)...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo   Проверка CDP
echo ========================================
python -c "import requests; r = requests.get('http://127.0.0.1:9222/json', timeout=5); print('✅ CDP доступен! Targets:', len(r.json()))" 2>nul

if errorlevel 1 (
    echo ❌ CDP недоступен
    echo Попробуйте перезапустить скрипт
) else (
    echo.
    echo ✅ Comet browser запущен с CDP!
    echo 📍 CDP URL: http://127.0.0.1:9222
    echo.
    echo Теперь можно запускать Comet extraction через фронтенд
)

echo.
pause
