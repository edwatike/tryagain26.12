"""
ПРОСТОЙ ВИЗУАЛЬНЫЙ ТЕСТ АССИСТЕНТА
Без сложной активации окна
"""
import pyautogui
import time
import pyperclip
import os

# Отключаем fail-safe
pyautogui.FAILSAFE = False

def take_screenshot(name: str) -> str:
    """Сделать скриншот."""
    try:
        screenshot = pyautogui.screenshot()
        filename = f"screenshot_{name}_{int(time.time())}.png"
        screenshot.save(filename)
        print(f"📸 Скриншот: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Ошибка скриншота: {e}")
        return ""

def simple_assistant_test():
    """Простой тест ассистента."""
    print("🚀 ПРОСТОЙ ВИЗУАЛЬНЫЙ ТЕСТ АССИСТЕНТА")
    print("="*50)
    
    # Скриншот ДО
    print("📍 Скриншот ДО открытия ассистента...")
    take_screenshot("before_assistant")
    
    # Alt+A
    print("📍 Нажимаю Alt+A...")
    pyautogui.hotkey('alt', 'a')
    time.sleep(3)
    
    # Скриншот ПОСЛЕ Alt+A
    print("📍 Скриншот ПОСЛЕ Alt+A...")
    take_screenshot("after_alt_a")
    
    # Пробуем разные позиции
    positions = [
        (1632, 993),  # Правый нижний
        (960, 540),   # Центр
        (1728, 540),  # Справа центр
        (1200, 800),  # Право-низ
        (700, 800),   # Лево-низ
    ]
    
    for i, (x, y) in enumerate(positions):
        print(f"\n🔄 Тест позиции {i+1}: ({x}, {y})")
        
        # Клик
        pyautogui.click(x, y)
        time.sleep(2)
        
        # Скриншот после клика
        take_screenshot(f"pos_{i+1}_after_click")
        
        # Пробуем ввод
        test_text = f"TEST_POSITION_{i+1}"
        pyperclip.copy(test_text)
        time.sleep(1)
        
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)
        
        # Скриншот после ввода
        take_screenshot(f"pos_{i+1}_after_input")
        
        # Проверяем
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        print(f"   📋 Буфер: '{clipboard}'")
        
        if test_text in clipboard:
            print(f"   ✅ ПОЗИЦИЯ {i+1} РАБОТАЕТ!")
            take_screenshot(f"pos_{i+1}_success")
            return True
        else:
            print(f"   ❌ Позиция {i+1} не работает")
    
    return False

def main():
    """Главная функция."""
    print("🚀 ПРОСТОЙ ВИЗУАЛЬНЫЙ ТЕСТ")
    print("="*50)
    print("📍 Убедитесь что Comet открыт и активен")
    print("📍 Не трогайте мышь и клавиатуру")
    print("\n🚀 Нажмите Enter для начала...")
    input()
    
    success = simple_assistant_test()
    
    print("\n📊 РЕЗУЛЬТАТ:")
    print("="*30)
    
    if success:
        print("✅ УСПЕХ! АССИСТЕНТ НАЙДЕН!")
        print("📸 Проверьте скриншоты:")
        print("   - screenshot_before_assistant_*.png")
        print("   - screenshot_after_alt_a_*.png")
        print("   - screenshot_pos_*_success.png")
        print("\n🎉 ВИДИТЕ ПОЛЕ ВВОДА НА СКРИНШОТАХ!")
    else:
        print("❌ НЕУСПЕХ! АССИСТЕНТ НЕ НАЙДЕН!")
        print("📸 Проверьте скриншоты чтобы понять что происходит")
    
    print(f"\n📍 Всего скриншотов: {len([f for f in os.listdir('.') if f.startswith('screenshot_')])}")

if __name__ == "__main__":
    main()
