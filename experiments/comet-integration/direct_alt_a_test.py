"""
ПРЯМАЯ ПРОВЕРКА ALT+A
"""
import pyautogui
import time

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ПРЯМАЯ ПРОВЕРКА ALT+A')
print('='*40)

print('📍 Буду нажимать Alt+A каждые 3 секунды')
print('📍 Смотрите что происходит в Comet')
print('📍 Нажмите Ctrl+C чтобы остановить')
print('='*40)

try:
    for i in range(10):
        print(f'🔄 Попытка {i+1}/10 - нажимаю Alt+A...')
        pyautogui.hotkey('alt', 'a')
        time.sleep(3)
        print(f'✅ Попытка {i+1} завершена')
except KeyboardInterrupt:
    print('\n⚠️ Тест прерван')

print('📍 Тест завершен')
