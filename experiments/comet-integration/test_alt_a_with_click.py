"""
ПРОВЕРКА ALT+A С КЛИКОМ
"""
import pyautogui
import time
import pyperclip

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ПРОВЕРКА ALT+A С КЛИКОМ')
print('='*40)

print('📍 Пробую кликнуть в центр страницы, потом Alt+A')

try:
    for i in range(5):
        print(f'🔄 Попытка {i+1}/5')
        
        # Клик в центр
        print('   📍 Клик в центр (960, 540)...')
        pyautogui.click(960, 540)
        time.sleep(1)
        
        # Alt+A
        print('   📍 Нажимаю Alt+A...')
        pyautogui.hotkey('alt', 'a')
        time.sleep(3)
        
        # Пробуем ввести
        print('   📍 Ввожу TEST...')
        pyautogui.typewrite('TEST', interval=0.1)
        time.sleep(2)
        
        # Проверяем
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        print(f'   📋 Результат: \"{clipboard}\"')
        
        if 'TEST' in clipboard:
            print('   ✅ УСПЕХ! Ассистент открыт!')
            break
        else:
            print('   ❌ Не работает')
        
        print()
        
except KeyboardInterrupt:
    print('\n⚠️ Тест прерван')

print('📍 Тест завершен')
