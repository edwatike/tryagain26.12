"""
ПРОВЕРКА ALT+A ДЛЯ АССИСТЕНТА
"""
import pyautogui
import time
import pyperclip
import pygetwindow as gw

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ПРОСТАЯ ПРОВЕРКА ALT+A')
print('='*50)

# Активируем Comet
windows = gw.getWindowsWithTitle('Comet')
if windows:
    windows[0].activate()
    time.sleep(2)
    print('✅ Comet активирован')
    
    # Alt+A
    print('📍 Нажимаю Alt+A...')
    pyautogui.hotkey('alt', 'a')
    time.sleep(3)
    
    # Ждем немного больше
    print('⏳ Жду 5 секунд...')
    time.sleep(5)
    
    # Пробуем ввести текст без клика
    print('📍 Ввожу TEST без клика...')
    pyautogui.typewrite('TEST', interval=0.1)
    time.sleep(2)
    
    # Проверяем
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    clipboard = pyperclip.paste()
    print(f'📋 В буфере: \"{clipboard}\"')
    
    if 'TEST' in clipboard:
        print('✅ АССИСТЕНТ ОТКРЫТ!')
    else:
        print('❌ Ассистент не открыт')
        print('📍 Пробую кликнуть в центр экрана...')
        pyautogui.click(960, 540)
        time.sleep(2)
        
        pyautogui.typewrite('TEST', interval=0.1)
        time.sleep(2)
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        print(f'📋 После клика в центр: \"{clipboard}\"')
        
        if 'TEST' in clipboard:
            print('✅ АССИСТЕНТ ОТКРЫТ ПОСЛЕ КЛИКА!')
        else:
            print('❌ Ассистент не найден')
else:
    print('❌ Comet не найден')
