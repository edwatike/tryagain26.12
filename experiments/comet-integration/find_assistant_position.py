"""
ПРОВЕРКА ГДЕ АССИСТЕНТ
"""
import pyautogui
import time
import pyperclip

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ПРОВЕРКА ГДЕ АССИСТЕНТ')
print('='*40)

print('📍 Пробую разные места после Alt+A')

# Разные места где может быть ассистент
positions = [
    (1632, 993),  # Правый нижний угол
    (960, 540),   # Центр
    (1728, 540),  # Справа центр
    (1200, 800),  # Право-низ
    (700, 800),   # Лево-низ
    (1632, 200),  # Справа вверху
    (960, 200),   # Центр вверху
]

try:
    for i, (x, y) in enumerate(positions):
        print(f'🔄 Тест {i+1}/{len(positions)}: ({x}, {y})')
        
        # Alt+A
        print('   📍 Нажимаю Alt+A...')
        pyautogui.hotkey('alt', 'a')
        time.sleep(3)
        
        # Клик в позицию
        print(f'   📍 Клик в ({x}, {y})...')
        pyautogui.click(x, y)
        time.sleep(2)
        
        # Вводим TEST
        print('   📍 Ввожу TEST...')
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.press('delete')
        time.sleep(0.5)
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
            print(f'   ✅ НАЙДЕНО! Ассистент в позиции ({x}, {y})!')
            print(f'   🎉 ПОЗИЦИЯ АССИСТЕНТА: ({x}, {y})')
            break
        else:
            print('   ❌ Не работает')
        
        print()
        
except KeyboardInterrupt:
    print('\n⚠️ Тест прерван')

print('📍 Тест завершен')
