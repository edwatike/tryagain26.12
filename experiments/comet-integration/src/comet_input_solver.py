"""
РЕШЕНИЕ ПРОБЛЕМЫ ВВОДА В COMET
Используем буфер обмена вместо pyautogui.typewrite
"""
import pyautogui
import time
import pyperclip
import pygetwindow as gw
import subprocess

# Отключаем fail-safe
pyautogui.FAILSAFE = False

class CometInputSolver:
    """Решатель проблемы ввода в Comet."""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        print(f'🚀 CometInputSolver инициализирован')
        print(f'🌐 Экран: {self.screen_width}x{self.screen_height}')
    
    def activate_comet(self) -> bool:
        """Активировать окно Comet."""
        try:
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                windows[0].activate()
                time.sleep(1)
                return True
            return False
        except:
            return False
    
    def open_assistant_clipboard_method(self) -> bool:
        """Открыть ассистента и проверить через буфер обмена."""
        try:
            print('📍 Открываю ассистента (Alt+A)...')
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Пробуем разные позиции для ввода через буфер обмена
            positions = [
                (1632, 993),  # Правый нижний
                (960, 540),   # Центр
                (1728, 540),  # Справа центр
                (1200, 800),  # Право-низ
            ]
            
            for i, (x, y) in enumerate(positions):
                print(f'🔄 Пробую позицию {i+1}: ({x}, {y})')
                
                # Клик
                pyautogui.click(x, y)
                time.sleep(1)
                
                # Очищаем через Ctrl+A, Delete
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.press('delete')
                time.sleep(0.5)
                
                # Копируем тест в буфер обмена
                test_text = f'CLIPBOARD_TEST_{i+1}'
                pyperclip.copy(test_text)
                time.sleep(0.5)
                
                # Вставляем через Ctrl+V
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(2)
                
                # Проверяем что вставилось
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                clipboard = pyperclip.paste()
                print(f'   📋 Результат: \"{clipboard}\"')
                
                if test_text in clipboard:
                    print(f'   ✅ УСПЕХ! Позиция ({x}, {y}) работает!')
                    return True
            
            return False
            
        except Exception as e:
            print(f'❌ Ошибка: {e}')
            return False
    
    def send_prompt_via_clipboard(self, prompt: str) -> bool:
        """Отправить промпт через буфер обмена."""
        try:
            print(f'📍 Отправляю промпт: {prompt}')
            
            # Копируем промпт в буфер обмена
            pyperclip.copy(prompt)
            time.sleep(0.5)
            
            # Находим рабочую позицию (из предыдущего теста)
            working_position = (1632, 993)  # Начнем с правого нижнего угла
            
            # Клик в позицию
            pyautogui.click(working_position[0], working_position[1])
            time.sleep(1)
            
            # Очищаем поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Вставляем промпт
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            # Проверяем что вставилось
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            clipboard = pyperclip.paste()
            print(f'📋 Введено: \"{clipboard[:100]}...\"')
            
            if prompt[:50] in clipboard:
                print('✅ Промпт введен!')
                
                # Отправляем
                pyautogui.press('enter')
                time.sleep(1)
                print('✅ Промпт отправлен!')
                return True
            else:
                print('❌ Промпт не введен')
                return False
                
        except Exception as e:
            print(f'❌ Ошибка отправки промпта: {e}')
            return False
    
    def get_response_via_clipboard(self, max_wait: int = 30) -> str:
        """Получить ответ через буфер обмена."""
        try:
            print(f'⏳ Ожидаю ответ {max_wait} секунд...')
            
            for i in range(max_wait):
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    print(f'   ⏳ Прошло {i + 1}/{max_wait} секунд...')
            
            print('📍 Получаю ответ...')
            
            # Alt+A чтобы убедиться что ассистент открыт
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Выделяем все и копируем
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            response = pyperclip.paste()
            print(f'📋 Получен ответ: {len(response)} символов')
            
            return response
            
        except Exception as e:
            print(f'❌ Ошибка получения ответа: {e}')
            return ""
    
    def full_cycle_test(self, domain: str) -> dict:
        """Полный цикл теста."""
        try:
            print(f'🚀 Полный цикл для {domain}')
            print('='*50)
            
            # Шаг 1: Активировать Comet
            if not self.activate_comet():
                return {"success": False, "error": "Не удалось активировать Comet"}
            
            # Шаг 2: Открыть ассистента
            if not self.open_assistant_clipboard_method():
                return {"success": False, "error": "Не удалось открыть ассистент"}
            
            # Шаг 3: Отправить промпт
            prompt = f'Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему.'
            if not self.send_prompt_via_clipboard(prompt):
                return {"success": False, "error": "Не удалось отправить промпт"}
            
            # Шаг 4: Получить ответ
            response = self.get_response_via_clipboard(30)
            
            if len(response) > 50:
                return {
                    "success": True,
                    "response": response,
                    "domain": domain
                }
            else:
                return {
                    "success": False,
                    "error": f"Ответ слишком короткий: {len(response)} символов",
                    "response": response
                }
                
        except Exception as e:
            return {"success": False, "error": f"Критическая ошибка: {e}"}


def main():
    """Главная функция."""
    print('🚀 РЕШЕНИЕ ПРОБЛЕМЫ ВВОДА В COMET')
    print('='*50)
    print('✅ Используем буфер обмена вместо typewrite')
    print('✅ Пробуем разные позиции для ввода')
    print('✅ Проверяем каждый шаг')
    print('='*50)
    
    solver = CometInputSolver()
    
    # Тест 1: Проверка открытия ассистента
    print('\n📍 ТЕСТ 1: Открытие ассистента')
    if solver.open_assistant_clipboard_method():
        print('✅ Ассистент открыт и готов к вводу!')
        
        # Тест 2: Полный цикл
        print('\n📍 ТЕСТ 2: Полный цикл')
        result = solver.full_cycle_test('metallsnab-nn.ru')
        
        if result["success"]:
            print('✅ ПОЛНЫЙ ЦИКЛ УСПЕШЕН!')
            print(f'📋 Ответ: {result["response"][:200]}...')
        else:
            print(f'❌ ПОЛНЫЙ ЦИКЛ НЕ УСПЕШЕН: {result["error"]}')
    else:
        print('❌ Не удалось открыть ассистент')


if __name__ == "__main__":
    main()
