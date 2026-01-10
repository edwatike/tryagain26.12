@echo off
chcp 65001 >nul
echo ========================================
echo   Shortcut /requisites Experiment
echo ========================================
echo.
echo 💡 Эксперимент с кастомным Shortcut в Comet
echo 🎯 Команда: /requisites
echo ⚡ Надежный способ извлечения ИНН и email
echo.
echo 📋 Домены (10 штук):
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
echo    ✅ Создан Shortcut /requisites в Comet
echo    ✅ pyautogui установлен
echo    ✅ Comet браузер готов
echo    ✅ НЕ трогать мышь/клавиатуру 10-15 минут
echo.
echo 🎯 Преимущества:
echo    ✅ Надежность - готовая команда
echo    ✅ Скорость - не нужно вводить промпты
echo    ✅ Точность - настроенный промпт
echo    ✅ Стабильность - меньше ошибок
echo.
echo ⏱️  Ожидаемое время: ~3-4 минуты
echo.

cd /d "%~dp0"

echo 🚀 Запуск эксперимента с Shortcut...
echo.

python src/shortcut_experiment.py

echo.
echo ========================================
echo   ЭКСПЕРИМЕНТ ЗАВЕРШЕН
echo ========================================
echo.
echo 📁 Результаты сохранены в папке data/
echo 📋 Файлы:
echo    - shortcut_results_*.json (полные результаты)
echo    - shortcut_clean_results_*.json (только ИНН+email+source_url)
echo.

pause
