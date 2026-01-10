@echo off
chcp 65001 >nul
echo ========================================
echo   Comet Integration Tests
echo ========================================
echo.

cd /d "%~dp0"

echo 🧪 Запуск тестов Comet клиента...
echo.

python tests/test_comet.py

echo.
echo ========================================
echo   Тесты завершены
echo ========================================
echo.

pause
