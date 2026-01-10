"""
Умный поиск поля ввода - программа сама определяет куда вводится текст.
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

def check_where_text_entered(test_text):
    """Проверить куда был введен текст."""
    try:
        # Получаем текст из буфера обмена
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        
        clipboard_content = pyperclip.paste()
        
        # Анализируем где появился текст
        if test_text in clipboard_content:
            # Проверяем это поле поиска или поле ввода
            if 'http' in clipboard_content or 'perplexity' in clipboard_content.lower():
                return "search"  # Поле поиска
            elif len(clipboard_content.strip()) == len(test_text):
                return "input"   # Поле ввода ассистента
            else:
                return "other"   # Другое место
        else:
            return "none"    # Ни где не появился
            
    except:
        return "error"

def smart_input_finder():
    """Умный поиск поля ввода."""
    print("🧠 УМНЫЙ ПОИСК ПОЛЯ ВВОДА")
    print("="*60)
    print("🎯 Программа сама определит куда вводится текст")
    print("✅ Без вопросов пользователю")
    print("🤖 Автоматическая проверка")
    print("="*60)
    
    screen_width, screen_height = pyautogui.size()
    print(f"📐 Размер экрана: {screen_width}x{screen_height}")
    
    # Ключевые точки для проверки
    test_points = [
        # Правая панель - низ
        (int(screen_width * 0.85), int(screen_height * 0.92)),  # Стандартное место
        (int(screen_width * 0.80), int(screen_height * 0.92)),  # Чуть левее
        (int(screen_width * 0.90), int(screen_height * 0.92)),  # Чуть правее
        
        # Правая панель - центр
        (int(screen_width * 0.85), int(screen_height * 0.85)),  # Выше
        (int(screen_width * 0.85), int(screen_height * 0.88)),  # Еще выше
        
        # Очень низ
        (int(screen_width * 0.85), int(screen_height * 0.95)),  # Самый низ
        (int(screen_width * 0.85), int(screen_height * 0.98)),  # Край экрана
        
        # Другие варианты
        (int(screen_width * 0.75), int(screen_height * 0.92)),  # Левее
        (int(screen_width * 0.95), int(screen_height * 0.92)),  # Край справа
    ]
    
    print(f"🎯 Проверю {len(test_points)} ключевых точек")
    
    for idx, (x, y) in enumerate(test_points):
        print(f"\n{'='*60}")
        print(f"🎯 ТОЧКА #{idx + 1}/{len(test_points)}")
        print(f"📍 Координаты: ({x}, {y})")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Активация Comet
            print("📍 Шаг 1: Активация Comet...")
            if not force_comet_focus():
                print("❌ Не удалось активировать Comet")
                continue
            
            time.sleep(1)
            if 'comet' not in get_active_window_title().lower():
                print("❌ Фокус не в Comet")
                continue
            
            # Шаг 2: Открыть ассистента
            print("📍 Шаг 2: Alt+A...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if 'comet' not in get_active_window_title().lower():
                print("❌ Фокус ушел после Alt+A")
                continue
            
            # Шаг 3: Визуальный клик
            print("📍 Шаг 3: Клик по точке...")
            pyautogui.moveTo(x, y, duration=0.3)
            time.sleep(0.3)
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            # Шаг 4: Тест ввода
            print("📍 Шаг 4: Тест ввода...")
            test_text = f"TEST_{idx + 1}_{int(time.time())}"
            
            # Очистка и ввод
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)
            pyautogui.typewrite(test_text, interval=0.02)
            time.sleep(0.5)
            
            # Шаг 5: Автоматическая проверка
            print("📍 Шаг 5: Автоматическая проверка...")
            result = check_where_text_entered(test_text)
            
            print(f"   📝 Введен текст: {test_text}")
            print(f"   🔍 Результат проверки: {result}")
            
            if result == "input":
                print(f"🎉 НАЙДЕНО! ТОЧКА #{idx + 1} РАБОТАЕТ!")
                print(f"✅ Это поле ввода ассистента!")
                print(f"🎯 Координаты: ({x}, {y})")
                
                # Очищаем поле
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                pyautogui.press('delete')
                time.sleep(0.2)
                
                print("="*60)
                print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                print("✅ Найдены координаты поля ввода ассистента!")
                print("="*60)
                return True, (x, y)
                
            elif result == "search":
                print("❌ Это поле поиска, не ассистент")
            elif result == "other":
                print("❌ Другое место, не ассистент")
            elif result == "none":
                print("❌ Текст не появился")
            elif result == "error":
                print("❌ Ошибка проверки")
            
            # Очищаем перед следующей точкой
            try:
                if 'comet' in get_active_window_title().lower():
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.2)
                    pyautogui.press('delete')
                    time.sleep(0.2)
            except:
                pass
            
            print(f"❌ Точка #{idx + 1} не подходит")
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Ошибка в точке #{idx + 1}: {e}")
            time.sleep(1)
    
    print(f"\n❌ ВСЕ ТОЧКИ ПРОВЕРЕНЫ!")
    print("❌ ПОЛЕ ВВОДА АССИСТЕНТА НЕ НАЙДЕНО!")
    return False, None

if __name__ == "__main__":
    print("🧠 ЗАПУСК УМНОГО ПОИСКА ПОЛЯ ВВОДА")
    print("🎯 Программа сама определит куда вводится текст")
    print("✅ Без вопросов пользователю")
    print()
    
    success, coordinates = smart_input_finder()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Найдены координаты поля ввода ассистента!")
        print(f"🎯 Координаты: {coordinates}")
        print("🚀 Можно использовать в основной программе!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Поле ввода ассистента не найдено")
        print("🔍 Возможно структура интерфейса отличается")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
