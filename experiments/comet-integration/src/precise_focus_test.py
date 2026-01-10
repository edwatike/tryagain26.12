"""
Тест с точными координатами поля ввода в Comet.
Находит правильное место для клика.
"""
import time
import pyautogui
import subprocess
import pyperclip
from pathlib import Path

def get_active_window_title():
    """Получить заголовок активного окна."""
    try:
        import pygetwindow as gw
        active = gw.getActiveWindow()
        return active.title if active else "Unknown"
    except:
        return "Error"

def verify_focus_in_comet():
    """Проверить что фокус именно в Comet."""
    active_title = get_active_window_title()
    return 'comet' in active_title.lower()

def force_comet_focus():
    """Принудительно вернуть фокус в Comet."""
    try:
        import pygetwindow as gw
        
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'comet' in win.title.lower():
                    windows = [win]
                    break
        
        if windows:
            window = windows[0]
            try:
                # PowerShell метод
                ps_command = f'''
                Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class Win32 {{
                    [DllImport("user32.dll")]
                    [return: MarshalAs(UnmanagedType.Bool)]
                    public static extern bool SetForegroundWindow(IntPtr hWnd);
                }}
"@
                $processes = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*Comet*" }}
                if ($processes) {{
                    $hwnd = $processes[0].MainWindowHandle
                    [Win32]::SetForegroundWindow($hwnd)
                }}
                '''
                subprocess.run(['powershell', '-Command', ps_command], timeout=3, capture_output=True)
                time.sleep(1)
                return True
            except:
                pass
        return False
    except:
        return False

def find_input_field_coordinates():
    """Найти координаты поля ввода ассистента."""
    print("🔍 ПОИСК КООРДИНАТ ПОЛЯ ВВОДА")
    
    screen_width, screen_height = pyautogui.size()
    print(f"📐 Размер экрана: {screen_width}x{screen_height}")
    
    # Различные стратегии поиска поля ввода
    strategies = [
        {
            "name": "Правая нижняя область (стандарт)",
            "x": int(screen_width * 0.85),  # 85% ширины
            "y": int(screen_height * 0.92),  # 92% высоты
            "description": "Центр правой панели внизу"
        },
        {
            "name": "Правая панель центр",
            "x": int(screen_width * 0.75),  # 75% ширины
            "y": int(screen_height * 0.80),  # 80% высоты
            "description": "Центр правой панели"
        },
        {
            "name": "Низ экрана центр",
            "x": int(screen_width * 0.50),  # 50% ширины
            "y": int(screen_height * 0.95),  # 95% высоты
            "description": "Самый низ экрана"
        },
        {
            "name": "Правый нижний угол",
            "x": int(screen_width * 0.95),  # 95% ширины
            "y": int(screen_height * 0.90),  # 90% высоты
            "description": "Правый нижний угол"
        }
    ]
    
    return strategies

def test_precise_focus():
    """Тест с точными координатами поля ввода."""
    print("🎯 ТЕСТ С ТОЧНЫМИ КООРДИНАТАМИ ПОЛЯ ВВОДА")
    print("="*60)
    print("🔍 Буду тестировать разные координаты поля ввода")
    print("✅ Найду рабочие координаты")
    print("="*60)
    
    strategies = find_input_field_coordinates()
    
    for strategy_idx, strategy in enumerate(strategies):
        print(f"\n{'='*60}")
        print(f"🎯 СТРАТЕГИЯ #{strategy_idx + 1}: {strategy['name']}")
        print(f"📍 Координаты: ({strategy['x']}, {strategy['y']})")
        print(f"📝 Описание: {strategy['description']}")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Активация Comet
            print("📍 Шаг 1: Активация Comet...")
            if not force_comet_focus():
                print("❌ Не удалось активировать Comet")
                continue
            
            time.sleep(1)
            if not verify_focus_in_comet():
                print("❌ Фокус не в Comet")
                continue
            
            print("✅ Comet активен")
            
            # Шаг 2: Открыть ассистента
            print("📍 Шаг 2: Alt+A...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if not verify_focus_in_comet():
                print("❌ Фокус ушел после Alt+A")
                continue
            
            # Шаг 3: Тестовый клик по координатам
            print("📍 Шаг 3: Клик по координатам...")
            print(f"   🎯 Кликаю в ({strategy['x']}, {strategy['y']})")
            
            # Сохраняем позицию курсора
            original_pos = pyautogui.position()
            
            # Кликаем по координатам
            pyautogui.click(strategy['x'], strategy['y'])
            time.sleep(0.5)
            
            # Проверяем фокус после клика
            if not verify_focus_in_comet():
                print("❌ Фокус ушел после клика!")
                print(f"   📍 Активное окно: {get_active_window_title()}")
                continue
            
            print("✅ Фокус в Comet после клика")
            
            # Шаг 4: Тест ввода
            print("📍 Шаг 4: Тест ввода...")
            test_text = f"TEST_{strategy_idx + 1}_{int(time.time())}"
            
            # Очищаем поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.3)
            pyautogui.press('delete')
            time.sleep(0.3)
            
            # Вводим текст
            pyautogui.typewrite(test_text, interval=0.05)
            time.sleep(1)
            
            # Шаг 5: Проверка результата
            print("📍 Шаг 5: Проверка результата...")
            
            try:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.3)
                
                clipboard_content = pyperclip.paste()
                
                if test_text in clipboard_content:
                    print(f"🎉 УСПЕХ СТРАТЕГИИ #{strategy_idx + 1}!")
                    print(f"✅ Текст '{test_text}' введен!")
                    print(f"📋 Полное содержимое: {clipboard_content}")
                    print(f"🎯 РАБОЧИЕ КООРДИНАТЫ: ({strategy['x']}, {strategy['y']})")
                    
                    # Очищаем поле
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.3)
                    pyautogui.press('delete')
                    time.sleep(0.3)
                    
                    print("="*60)
                    print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                    print("✅ Найдены рабочие координаты поля ввода!")
                    print("="*60)
                    return True, strategy
                else:
                    print(f"❌ Текст не найден")
                    print(f"📝 Ожидали: {test_text}")
                    print(f"📝 Получили: {clipboard_content}")
                    
            except Exception as e:
                print(f"❌ Ошибка проверки: {e}")
            
            # Очищаем перед следующей стратегией
            try:
                if verify_focus_in_comet():
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.3)
                    pyautogui.press('delete')
                    time.sleep(0.3)
            except:
                pass
            
            print(f"❌ Стратегия #{strategy_idx + 1} не удалась")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Ошибка в стратегии #{strategy_idx + 1}: {e}")
            time.sleep(2)
    
    print(f"\n❌ ВСЕ СТРАТЕГИИ ИСЧЕРПАНЫ!")
    print("❌ РАБОЧИЕ КООРДИНАТЫ НЕ НАЙДЕНЫ!")
    return False, None

if __name__ == "__main__":
    print("🎯 ЗАПУСК ТЕСТА С ТОЧНЫМИ КООРДИНАТАМИ")
    print("🔍 Поиск рабочих координат поля ввода в Comet")
    print()
    
    success, working_strategy = test_precise_focus()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Найдены рабочие координаты поля ввода!")
        print(f"🎯 Координаты: ({working_strategy['x']}, {working_strategy['y']})")
        print(f"📝 Стратегия: {working_strategy['name']}")
        print("🚀 Можно использовать эти координаты в основной программе!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Нужно проверять структуру интерфейса Comet")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
