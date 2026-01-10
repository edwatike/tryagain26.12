"""
ВИЗУАЛЬНЫЙ ТЕСТ ОТКРЫТИЯ АССИСТЕНТА
Показываем что ассистент реально открывается
"""
import pyautogui
import time
import pyperclip
import pygetwindow as gw
import subprocess
from PIL import Image, ImageDraw
import os

# Отключаем fail-safe
pyautogui.FAILSAFE = False

class VisualAssistantTester:
    """Визуальный тестер ассистента."""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.assistant_x = int(self.screen_width * 0.85)
        self.assistant_y = int(self.screen_height * 0.92)
        
        print(f'🚀 VisualAssistantTester инициализирован')
        print(f'🌐 Экран: {self.screen_width}x{self.screen_height}')
        print(f'🎯 Позиция ассистента: ({self.assistant_x}, {self.assistant_y})')
    
    def take_screenshot(self, name: str) -> str:
        """Сделать скриншот."""
        try:
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{name}_{int(time.time())}.png"
            filepath = os.path.join(os.getcwd(), filename)
            screenshot.save(filepath)
            print(f"📸 Скриншот сохранен: {filename}")
            return filepath
        except Exception as e:
            print(f"❌ Ошибка скриншота: {e}")
            return ""
    
    def activate_comet_and_screenshot(self) -> bool:
        """Активировать Comet и сделать скриншот."""
        try:
            print("📍 Активирую Comet...")
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                windows[0].activate()
                time.sleep(2)
                print("✅ Comet активирован")
                
                # Скриншот ДО открытия ассистента
                self.take_screenshot("before_assistant")
                return True
            else:
                print("❌ Comet не найден")
                return False
        except Exception as e:
            print(f"❌ Ошибка активации: {e}")
            return False
    
    def open_assistant_with_visual_check(self) -> bool:
        """Открыть ассистента с визуальной проверкой."""
        try:
            print("📍 Нажимаю Alt+A...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Скриншот ПОСЛЕ Alt+A
            self.take_screenshot("after_alt_a")
            
            print("📍 Кликаю в позицию ассистента...")
            pyautogui.click(self.assistant_x, self.assistant_y)
            time.sleep(2)
            
            # Скриншот ПОСЛЕ клика
            self.take_screenshot("after_click")
            
            # Пробуем ввести тестовый текст
            print("📍 Ввожу тестовый текст...")
            test_text = "ASSISTANT_OPENED_VISUAL_TEST"
            pyperclip.copy(test_text)
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            # Скриншот ПОСЛЕ ввода
            self.take_screenshot("after_input")
            
            # Проверяем что введено
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            clipboard = pyperclip.paste()
            print(f"📋 В буфере: '{clipboard}'")
            
            if test_text in clipboard:
                print("✅ АССИСТЕНТ ОТКРЫТ И РАБОТАЕТ!")
                
                # Финальный скриншот
                self.take_screenshot("assistant_working")
                return True
            else:
                print("❌ Ассистент не откликнулся на ввод")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка открытия ассистента: {e}")
            return False
    
    def test_different_positions(self) -> bool:
        """Пробуем разные позиции для ассистента."""
        positions = [
            (1632, 993),  # Правый нижний
            (960, 540),   # Центр
            (1728, 540),  # Справа центр
            (1200, 800),  # Право-низ
            (700, 800),   # Лево-низ
        ]
        
        for i, (x, y) in enumerate(positions):
            print(f"\n🔄 Тест позиции {i+1}/{len(positions)}: ({x}, {y})")
            
            # Alt+A
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Скриншот после Alt+A
            self.take_screenshot(f"pos_{i+1}_after_alt_a")
            
            # Клик в позицию
            pyautogui.click(x, y)
            time.sleep(2)
            
            # Скриншот после клика
            self.take_screenshot(f"pos_{i+1}_after_click")
            
            # Пробуем ввод
            test_text = f"TEST_POS_{i+1}"
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
            print(f"   📋 Результат: '{clipboard}'")
            
            if test_text in clipboard:
                print(f"   ✅ ПОЗИЦИЯ {i+1} РАБОТАЕТ!")
                self.take_screenshot(f"pos_{i+1}_working")
                return True
            else:
                print(f"   ❌ Позиция {i+1} не работает")
        
        return False
    
    def full_visual_test(self) -> bool:
        """Полный визуальный тест."""
        print("🚀 ПОЛНЫЙ ВИЗУАЛЬНЫЙ ТЕСТ АССИСТЕНТА")
        print("="*60)
        
        # Шаг 1: Активировать Comet и скриншот
        if not self.activate_comet_and_screenshot():
            return False
        
        # Шаг 2: Попробовать основную позицию
        print("\n📍 ТЕСТ ОСНОВНОЙ ПОЗИЦИИ")
        if self.open_assistant_with_visual_check():
            return True
        
        # Шаг 3: Пробуем другие позиции
        print("\n📍 ТЕСТ РАЗНЫХ ПОЗИЦИЙ")
        return self.test_different_positions()
    
    def show_results(self):
        """Показать результаты."""
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print("="*40)
        print("📸 Созданы скриншоты:")
        print("   - screenshot_before_assistant_*.png")
        print("   - screenshot_after_alt_a_*.png") 
        print("   - screenshot_after_click_*.png")
        print("   - screenshot_after_input_*.png")
        print("   - screenshot_assistant_working_*.png (если успешно)")
        print("   - screenshot_pos_*_*.png (тесты позиций)")
        print("\n📍 Откройте скриншоты чтобы увидеть:")
        print("   ✅ Как выглядит Comet до открытия ассистента")
        print("   ✅ Что происходит после Alt+A")
        print("   ✅ Где появляется поле ввода")
        print("   ✅ Работает ли ввод текста")
        print("\n🎯 Если видите поле ввода на скриншотах - ассистент открыт!")


def main():
    """Главная функция."""
    print("🚀 ВИЗУАЛЬНЫЙ ТЕСТ ОТКРЫТИЯ АССИСТЕНТА")
    print("="*60)
    print("✅ Показываем скриншотами что ассистент открывается")
    print("✅ Тестируем разные позиции")
    print("✅ Визуальное подтверждение работы")
    print("="*60)
    
    print("\n📍 Убедитесь что:")
    print("   ✅ Comet открыт")
    print("   ✅ Страница загружена")
    print("   ✅ Не переключайтесь на другие окна")
    print("\n🚀 Нажмите Enter для начала теста...")
    input()
    
    tester = VisualAssistantTester()
    
    success = tester.full_visual_test()
    
    tester.show_results()
    
    if success:
        print("\n🎉 УСПЕХ! АССИСТЕНТ ОТКРЫВАЕТСЯ!")
        print("✅ Проверьте скриншоты для визуального подтверждения")
    else:
        print("\n❌ НЕУСПЕХ! АССИСТЕНТ НЕ ОТКРЫВАЕТСЯ")
        print("📋 Проверьте скриншоты чтобы понять что происходит")
    
    print("\n📍 Скриншоты сохранены в текущей папке")


if __name__ == "__main__":
    main()
