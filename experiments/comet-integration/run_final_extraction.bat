@echo off
chcp 65001 >nul
echo ========================================
echo   FINAL EXTRACTION EXPERIMENT
echo ========================================
echo.
echo 🎯 Цель: извлечь ИНН + email + source_url
echo 📝 10 реальных доменов из результатов парсинга
echo ⏱️  Время: ~2-3 минуты
echo.
echo 📋 Домены:
echo    1. metallsnab-nn.ru
echo    2. wodoprovod.ru
echo    3. ozon.ru
echo    4. gremir.ru
echo    5. spb.lemanapro.ru
echo    6. lunda.ru
echo    7. kranikoff.ru
echo    8. santech.ru
echo    9. onyxspb.ru
echo   10. tehprommarket.ru
echo.
echo ⚠️  ВАЖНО:
echo    ✅ pyautogui установлен
echo    ✅ Comet браузер готов
echo    ✅ НЕ трогать мышь/клавиатуру
echo    ✅ Браузер будет переключаться автоматически
echo.
echo 🎯 Результат: JSON с domain + inn + email + source_url
echo.

cd /d "%~dp0"

echo 🚀 Запуск финального эксперимента...
echo.

python src/final_extraction.py

echo.
echo ========================================
echo   ЭКСПЕРИМЕНТ ЗАВЕРШЕН
echo ========================================
echo.
echo 📁 Проверьте результаты в папке data/
echo 📋 Файл: extraction_results_*.json
echo.

pause
