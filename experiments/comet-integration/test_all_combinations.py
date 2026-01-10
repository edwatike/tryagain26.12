"""
ПРОВЕРКА РАЗНЫХ КОМБИНАЦИЙ ДЛЯ АССИСТЕНТА
"""
import pyautogui
import time
import pyperclip
import pygetwindow as gw

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ПРОВЕРКА РАЗНЫХ КОМБИНАЦИЙ ДЛЯ АССИСТЕНТА')
print('='*60)

# Активируем Comet
windows = gw.getWindowsWithTitle('Comet')
if windows:
    windows[0].activate()
    time.sleep(2)
    print('✅ Comet активирован')
    
    # Пробуем разные комбинации
    combinations = [
        ('Alt+A', lambda: pyautogui.hotkey('alt', 'a')),
        ('Ctrl+Shift+A', lambda: pyautogui.hotkey('ctrl', 'shift', 'a')),
        ('Ctrl+Alt+A', lambda: pyautogui.hotkey('ctrl', 'alt', 'a')),
        ('F1', lambda: pyautogui.press('f1')),
        ('Ctrl+/', lambda: pyautogui.hotkey('ctrl', '/')),
        ('Ctrl+K', lambda: pyautogui.hotkey('ctrl', 'k')),
        ('Ctrl+I', lambda: pyautogui.hotkey('ctrl', 'i')),
        ('Alt+I', lambda: pyautogui.hotkey('alt', 'i')),
        ('Alt+Q', lambda: pyautogui.hotkey('alt', 'q')),
        ('Ctrl+Space', lambda: pyautogui.hotkey('ctrl', 'space')),
    ]
    
    for name, func in combinations:
        print(f'\n🔄 Пробую {name}...')
        
        # Очищаем перед тестом
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.press('delete')
        time.sleep(0.5)
        
        # Выполняем комбинацию
        func()
        time.sleep(3)
        
        # Пробуем ввести TEST
        pyautogui.typewrite('TEST', interval=0.1)
        time.sleep(2)
        
        # Проверяем результат
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        print(f'   📋 Результат: \"{clipboard}\"')
        
        if 'TEST' in clipboard:
            print(f'   ✅ {name} РАБОТАЕТ!')
            print(f'   🎉 АССИСТЕНТ НАЙДЕН ЧЕРЕЗ {name}!')
            break
        else:
            print(f'   ❌ {name} не работает')
    
    print('\n🔍 Пробую кликнуть в разные места после Alt+A...')
    
    # Пробуем Alt+A + клики
    pyautogui.hotkey('alt', 'a')
    time.sleep(3)
    
    positions = [
        (1632, 993),  # Правый нижний
        (960, 540),   # Центр
        (1728, 540),  # Справа центр
        (1200, 800),  # Право-низ
        (700, 800),   # Лево-низ
    ]
    
    for i, (x, y) in enumerate(positions):
        print(f'🔄 Клик {i+1}/5: ({x}, {y})')
        pyautogui.click(x, y)
        time.sleep(2)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.press('delete')
        time.sleep(0.5)
        pyautogui.typewrite('TEST', interval=0.1)
        time.sleep(2)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        if 'TEST' in clipboard:
            print(f'   ✅ НАЙДЕНО в позиции {i+1}: ({x}, {y})!')
            break
        else:
            print(f'   ❌ Позиция {i+1} не работает')
    
else:
    print('❌ Comet не найден')
