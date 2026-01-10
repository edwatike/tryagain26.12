@echo off
chcp 65001 >nul
echo ========================================
echo   Real Domain Extraction Experiment
echo ========================================
echo.
echo 💡 Эксперимент с 10 реальными доменами из парсинга
echo 💡 Цель: найти ИНН + email + source_url
echo.
echo 📝 Домены:
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
echo ⚠️  Важно:
echo    ✅ Убедитесь, что pyautogui установлен
echo    ✅ Comet браузер установлен и готов
echo    ✅ Не будете трогать мышь/клавиатуру 10-15 минут
echo    ✅ Браузер будет автоматически переключаться между доменами
echo.
echo 🎯 Ожидаемое время: ~2-3 минуты
echo.

cd /d "%~dp0"

echo 🚀 Запуск эксперимента с реальными доменами...
echo.

python src/real_domain_experiment.py

echo.
echo ========================================
echo   Эксперимент завершен
echo ========================================
echo.
echo 📁 Результаты сохранены в папке data/
echo 📋 Логи доступны в logs/experiment.log
echo 📊 Проверьте файлы:
echo    - real_domain_results_*.json (полные результаты)
echo    - clean_results_*.json (только ИНН+email+source_url)
echo.

pause
