@echo off
chcp 65001 >nul
title INN Agent Demo - Поиск ИНН на сайте
color 0A

echo ========================================
echo   INN Agent Demo - Поиск ИНН на сайте
echo ========================================
echo.

REM Get script directory
cd /d %~dp0

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import playwright, requests, httpx, fastapi" 2>nul
if errorlevel 1 (
    echo [INFO] Установка зависимостей...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [ERROR] Не удалось установить зависимости
        pause
        exit /b 1
    )
    echo [INFO] Установка браузеров Playwright...
    playwright install chromium --quiet
    if errorlevel 1 (
        echo [WARNING] Не удалось установить браузеры Playwright, но продолжаем...
    )
    echo [OK] Зависимости установлены
    echo.
) else (
    echo [OK] Зависимости установлены
    echo.
)

REM Ask for domain
echo ========================================
echo   Введите домен сайта для поиска ИНН
echo ========================================
echo.
echo Примеры:
echo   - example.com
echo   - www.obi.ru
echo   - https://example.com
echo.
set /p DOMAIN="Домен: "

REM Check if domain is empty
if "%DOMAIN%"=="" (
    echo.
    echo [ERROR] Домен не указан!
    pause
    exit /b 1
)

REM Clear screen and show header
cls
color 0A
echo ========================================
echo   INN Agent Demo - Поиск ИНН
echo ========================================
echo Домен: %DOMAIN%
echo ========================================
echo.

REM Run the program with the domain
python main.py "%DOMAIN%" --log-level DEBUG

REM Capture exit code
set EXIT_CODE=%errorlevel%

echo.
echo ========================================
if %EXIT_CODE%==0 (
    echo   Поиск завершен успешно
) else (
    echo   Поиск завершен с ошибкой (код: %EXIT_CODE%)
)
echo ========================================
echo.
pause

exit /b %EXIT_CODE%

