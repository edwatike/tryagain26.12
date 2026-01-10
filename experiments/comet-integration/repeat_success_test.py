"""
ПОВТОР УСПЕШНОГО ТЕСТА
Точно повторяем последовательность которая сработала
"""
import pyautogui
import time
import pyperclip

# Отключаем fail-safe
pyautogui.FAILSAFE = False

def repeat_successful_test():
    """Повторяем успешный тест."""
    print("🚀 ПОВТОР УСПЕШНОГО ТЕСТА")
    print("="*50)
    print("📍 Точно повторяем последовательность")
    print("📍 Как в визуальном тесте который сработал")
    print("="*50)
    
    # Точно как в успешном тесте
    positions = [
        (1632, 993),  # Позиция 1
        (960, 540),   # Позиция 2  
        (1728, 540),  # Позиция 3 - УСПЕШНАЯ!
        (1200, 800),  # Позиция 4
        (700, 800),   # Позиция 5
    ]
    
    print("📍 Alt+A...")
    pyautogui.hotkey('alt', 'a')
    time.sleep(3)
    
    for i, (x, y) in enumerate(positions):
        print(f"\n🔄 Тест позиции {i+1}: ({x}, {y})")
        
        # Клик
        pyautogui.click(x, y)
        time.sleep(2)
        
        # Пробуем ввод
        test_text = f"TEST_POSITION_{i+1}"
        pyperclip.copy(test_text)
        time.sleep(1)
        
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)
        
        # Проверяем
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        clipboard = pyperclip.paste()
        print(f"   📋 Буфер: '{clipboard}'")
        
        if test_text in clipboard:
            print(f"   ✅ ПОЗИЦИЯ {i+1} РАБОТАЕТ!")
            
            # Теперь пробуем полный цикл с этой позицией
            print(f"\n🚀 ПОЛНЫЙ ЦИКЛ С ПОЗИЦИЕЙ {i+1}")
            
            # Очищаем
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Вводим промпт
            prompt = "Найди ИНН и email для metallsnab-nn.ru"
            print(f"📍 Промпт: {prompt}")
            pyperclip.copy(prompt)
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            # Отправляем
            pyautogui.press('enter')
            time.sleep(1)
            print("✅ Промпт отправлен!")
            
            # Ждем ответ
            print("⏳ Жду ответ 30 секунд...")
            for j in range(30):
                time.sleep(1)
                if (j + 1) % 5 == 0:
                    print(f"   ⏳ {j + 1}/30")
            
            # Получаем ответ
            print("📍 Получаю ответ...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            pyautogui.click(x, y)
            time.sleep(2)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            response = pyperclip.paste()
            print(f"📋 Ответ: {response[:100]}...")
            
            return True
        else:
            print(f"   ❌ Позиция {i+1} не работает")
    
    return False

def main():
    """Главная функция."""
    print("🚀 ПОВТОР УСПЕШНОГО ТЕСТА")
    print("="*30)
    print("📍 Comet должен быть открыт")
    print("📍 Не трогать мышь/клавиатуру")
    print("\n🚀 Нажмите Enter...")
    input()
    
    success = repeat_successful_test()
    
    print("\n📊 РЕЗУЛЬТАТ:")
    print("="*20)
    
    if success:
        print("✅ УСПЕХ! НАЙДЕНА РАБОЧАЯ ПОЗИЦИЯ!")
        print("🎉 ПРОГРАММА ОТКРЫВАЕТ АССИСТЕНТА!")
        print("🎉 ПРОГРАММА ВВОДИТ ТЕКСТ!")
        print("🎉 ПРОГРАММА ПОЛУЧАЕТ ОТВЕТ!")
    else:
        print("❌ НИ ОДНА ПОЗИЦИЯ НЕ РАБОТАЕТ")
        print("📋 Возможно ассистент не открывается")

if __name__ == "__main__":
    main()
