"""
Тест который гарантированно проверяет что команды выполняются в Comet.
Проверяет активное окно перед каждой командой.
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

def force_activate_comet():
    """Принудительно активировать Comet."""
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
            print(f"📁 Найдено окно: {window.title}")
            
            # Метод 1: PowerShell
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
                subprocess.run(['powershell', '-Command', ps_command], timeout=5, capture_output=True)
                time.sleep(2)
                return True
            except:
                pass
            
            # Метод 2: Клик по центру
            try:
                center_x = window.left + window.width // 2
                center_y = window.top + window.height // 2
                pyautogui.click(center_x, center_y)
                time.sleep(2)
                return True
            except:
                pass
        
        return False
    except:
        return False

def verify_comet_active():
    """Проверить что Comet активен."""
    active_title = get_active_window_title()
    is_comet = 'comet' in active_title.lower()
    print(f"🔍 Активное окно: {active_title}")
    print(f"✅ Comet активен: {is_comet}")
    return is_comet

def comet_command_test():
    """Тест команд в Comet."""
    print("🎯 ТЕСТ КОМАНД В COMET")
    print("="*60)
    print("🎯 Гарантированная проверка что команды выполняются в Comet")
    print("✅ Проверка активного окна перед каждой командой")
    print("="*60)
    
    screen_width, screen_height = pyautogui.size()
    print(f"📐 Размер экрана: {screen_width}x{screen_height}")
    
    # Тестовые координаты
    test_points = [
        (int(screen_width * 0.85), int(screen_height * 0.92)),  # Стандарт
        (int(screen_width * 0.80), int(screen_height * 0.92)),  # Левее
        (int(screen_width * 0.90), int(screen_height * 0.92)),  # Правее
    ]
    
    for point_idx, (x, y) in enumerate(test_points):
        print(f"\n{'='*60}")
        print(f"🎯 ТОЧКА #{point_idx + 1}/{len(test_points)}")
        print(f"📍 Координаты: ({x}, {y})")
        print(f"{'='*60}")
        
        try:
            # ШАГ 1: ГАРАНТИРОВАННАЯ АКТИВАЦИЯ COMET
            print("📍 Шаг 1: Гарантированная активация Comet...")
            if not force_activate_comet():
                print("❌ Не удалось активировать Comet")
                continue
            
            # ШАГ 2: ПРОВЕРКА ЧТО COMET АКТИВЕН
            print("📍 Шаг 2: Проверка активности Comet...")
            if not verify_comet_active():
                print("❌ Comet не активен после активации!")
                continue
            
            # ШАГ 3: Alt+A - ПРОВЕРКА ЧТО В COMET
            print("📍 Шаг 3: Alt+A в Comet...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet после Alt+A!")
                continue
            
            # ШАГ 4: КЛИК - ПРОВЕРКА ЧТО В COMET
            print("📍 Шаг 4: Клик по координатам в Comet...")
            print(f"   🎯 Кликаю в ({x}, {y})")
            
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.5)
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet после клика!")
                continue
            
            # ШАГ 5: ОЧИСТКА - ПРОВЕРКА ЧТО В COMET
            print("📍 Шаг 5: Очистка поля в Comet...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet после Ctrl+A!")
                continue
            
            pyautogui.press('delete')
            time.sleep(0.5)
            
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet после очистки!")
                continue
            
            # ШАГ 6: ВВОД - ПРОВЕРКА ЧТО В COMET
            print("📍 Шаг 6: Ввод текста в Comet...")
            test_text = f"COMET_CMD_{point_idx + 1}"
            
            # Вводим текст с проверкой после каждого символа
            for i, char in enumerate(test_text):
                pyautogui.typewrite(char, interval=0.1)
                time.sleep(0.1)
                
                # Проверяем что фокус не ушел
                if i % 3 == 2:  # Проверяем каждый 3-й символ
                    if not verify_comet_active():
                        print(f"❌ Фокус ушел на символе {i+1}!")
                        break
            
            time.sleep(1)
            
            # ШАГ 7: ФИНАЛЬНАЯ ПРОВЕРКА
            print("📍 Шаг 7: Финальная проверка...")
            if not verify_comet_active():
                print("❌ Фокус ушел после ввода текста!")
                continue
            
            # ШАГ 8: ПРОВЕРКА ТЕКСТА
            print("📍 Шаг 8: Проверка введенного текста...")
            
            try:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                clipboard_content = pyperclip.paste()
                
                print(f"   📝 Ожидали: {test_text}")
                print(f"   📋 Получили: {clipboard_content}")
                
                if test_text in clipboard_content:
                    print(f"🎉 УСПЕХ ТОЧКИ #{point_idx + 1}!")
                    print(f"✅ Текст '{test_text}' введен в Comet!")
                    print(f"🎯 РАБОЧИЕ КООРДИНАТЫ: ({x}, {y})")
                    
                    # Очищаем
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
                    
                    print("="*60)
                    print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                    print("✅ КОМАНДЫ ВЫПОЛНЯЮТСЯ В COMET!")
                    print("="*60)
                    return True, (x, y)
                else:
                    print("❌ Текст не найден или не полный")
                    
            except Exception as e:
                print(f"❌ Ошибка проверки текста: {e}")
            
            # Очищаем перед следующей точкой
            try:
                if verify_comet_active():
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
            except:
                pass
            
            print(f"❌ Точка #{point_idx + 1} не подходит")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Ошибка в точке #{point_idx + 1}: {e}")
            time.sleep(2)
    
    print(f"\n❌ ВСЕ ТОЧКИ ПРОВЕРЕНЫ!")
    print("❌ КОМАНДЫ НЕ ВЫПОЛНЯЮТСЯ В COMET!")
    return False, None

if __name__ == "__main__":
    print("🎯 ЗАПУСК ТЕСТА КОМАНД В COMET")
    print("🎯 Гарантированная проверка что команды выполняются в Comet")
    print()
    
    print("⚠️ ВАЖНО:")
    print("   1. Убедитесь что Comet открыт")
    print("   2. Не переключайтесь в другие окна")
    print("   3. Программа будет проверять активное окно")
    print()
    
    input("Нажмите Enter когда готовы...")
    
    success, coordinates = comet_command_test()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Команды выполняются в Comet!")
        print(f"🎯 Рабочие координаты: {coordinates}")
        print("🚀 МОЖНО ИСПОЛЬЗОВАТЬ В ОСНОВНОЙ ПРОГРАММЕ!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Команды не выполняются в Comet")
        print("🔍 Нужно решать проблемы с фокусом")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
