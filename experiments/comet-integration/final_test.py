"""
ФИНАЛЬНЫЙ ТЕСТ - ЧТО РАБОТАЕТ
"""
import pyautogui
import time
import pyperclip

# Отключаем fail-safe
pyautogui.FAILSAFE = False

print('🔍 ФИНАЛЬНЫЙ ТЕСТ - ЧТО РАБОТАЕТ')
print('='*50)

# Тест 1: Базовый ввод в адресную строку
print('📍 ТЕСТ 1: Ввод в адресную строку')
try:
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.press('delete')
    time.sleep(0.5)
    pyautogui.typewrite('test.com', interval=0.1)
    time.sleep(2)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    clipboard = pyperclip.paste()
    print(f'   📋 В адресной строке: \"{clipboard}\"')
    
    if 'test.com' in clipboard:
        print('   ✅ Ввод в адресную строку работает!')
    else:
        print('   ❌ Ввод в адресную строку не работает')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()

# Тест 2: Ввод в поле поиска на странице
print('📍 ТЕСТ 2: Ввод в поле поиска на странице')
try:
    pyautogui.click(960, 300)  # Клик в центр страницы
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'f')  # Поиск на странице
    time.sleep(1)
    pyautogui.typewrite('search', interval=0.1)
    time.sleep(2)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    clipboard = pyperclip.paste()
    print(f'   📋 В поиске: \"{clipboard}\"')
    
    if 'search' in clipboard:
        print('   ✅ Ввод в поиск работает!')
    else:
        print('   ❌ Ввод в поиск не работает')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()

# Тест 3: Просто ввод без клика
print('📍 ТЕСТ 3: Простой ввод без клика')
try:
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.press('delete')
    time.sleep(0.5)
    pyautogui.typewrite('simple_test', interval=0.1)
    time.sleep(2)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    clipboard = pyperclip.paste()
    print(f'   📋 Простой ввод: \"{clipboard}\"')
    
    if 'simple_test' in clipboard:
        print('   ✅ Простой ввод работает!')
    else:
        print('   ❌ Простой ввод не работает')
except Exception as e:
    print(f'   ❌ Ошибка: {e}')

print()

# Тест 4: Проверка мыши
print('📍 ТЕСТ 4: Проверка работы мыши')
try:
    print('   📍 Двигаю мышь в углы экрана...')
    pyautogui.moveTo(100, 100, duration=1)
    time.sleep(0.5)
    pyautogui.moveTo(1820, 100, duration=1)
    time.sleep(0.5)
    pyautogui.moveTo(1820, 980, duration=1)
    time.sleep(0.5)
    pyautogui.moveTo(100, 980, duration=1)
    time.sleep(0.5)
    pyautogui.moveTo(960, 540, duration=1)
    print('   ✅ Мышь работает!')
except Exception as e:
    print(f'   ❌ Ошибка мыши: {e}')

print()
print('📊 РЕЗУЛЬТАТЫ ТЕСТОВ:')
print('📍 Если ввод в адресную строку работает - проблема в ассистенте')
print('📍 Если ничего не работает - проблема в pyautogui/Comet')
print('📍 Если мышь не работает - проблема в системе')
