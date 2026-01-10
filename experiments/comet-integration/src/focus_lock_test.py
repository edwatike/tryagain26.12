"""
Тест который постоянно проверяет что фокус в Comet.
Блокирует любые переключения в другие окна.
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
        
        # Ищем окна Comet
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'comet' in win.title.lower():
                    windows = [win]
                    break
        
        if windows:
            window = windows[0]
            
            # Принудительная активация
            try:
                # Метод 1: PowerShell
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
            
            # Метод 2: Клик по центру
            try:
                center_x = window.left + window.width // 2
                center_y = window.top + window.height // 2
                pyautogui.click(center_x, center_y)
                time.sleep(1)
                return True
            except:
                pass
        
        return False
    except:
        return False

def verify_focus_in_comet():
    """Проверить что фокус именно в Comet."""
    active_title = get_active_window_title()
    return 'comet' in active_title.lower()

def lock_focus_test():
    """Тест с блокировкой фокуса в Comet."""
    print("🔒 ТЕСТ С БЛОКИРОВКОЙ ФОКУСА В COMET")
    print("="*60)
    print("🎯 Фокус будет заблокирован в Comet")
    print("❌ Никаких переключений в другие окна!")
    print("⚠️ НЕ ПЕРЕКЛЮЧАЙТЕСЬ В ДРУГИЕ ОКНА!")
    print("="*60)
    
    attempt = 0
    max_attempts = 15
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"🔄 ПОПЫТКА #{attempt}")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Принудительная активация Comet
            print("📍 Шаг 1: Принудительная активация Comet...")
            if not force_comet_focus():
                print("❌ Не удалось активировать Comet")
                time.sleep(2)
                continue
            
            # Шаг 2: Проверка фокуса (КРИТИЧЕСКИ ВАЖНО!)
            print("📍 Шаг 2: Проверка фокуса...")
            time.sleep(1)  # Даем время на стабилизацию
            
            if not verify_focus_in_comet():
                print("❌ Фокус не в Comet!")
                print(f"📝 Активное окно: {get_active_window_title()}")
                print("⚠️ НЕ ПЕРЕКЛЮЧАЙТЕСЬ В ДРУГИЕ ОКНА!")
                time.sleep(3)
                continue
            
            print("✅ Фокус в Comet подтвержден")
            
            # Шаг 3: Открытие ассистента
            print("📍 Шаг 3: Alt+A...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 4: ПРОВЕРКА ФОКУСА ПОСЛЕ ALT+A!
            print("📍 Шаг 4: Проверка фокуса после Alt+A...")
            if not verify_focus_in_comet():
                print("❌ Фокус ушел из Comet после Alt+A!")
                print("🔄 Возвращаю фокус...")
                if not force_comet_focus():
                    print("❌ Не удалось вернуть фокус")
                    continue
                time.sleep(1)
            
            # Шаг 5: Клик по полю ввода
            print("📍 Шаг 5: Клик по полю ввода...")
            screen_width, screen_height = pyautogui.size()
            assistant_panel_x = int(screen_width * 0.8)
            assistant_input_y = int(screen_height * 0.92)
            
            pyautogui.click(assistant_panel_x, assistant_input_y)
            time.sleep(0.5)
            
            # Шаг 6: ПРОВЕРКА ФОКУСА ПОСЛЕ КЛИКА!
            print("📍 Шаг 6: Проверка фокуса после клика...")
            if not verify_focus_in_comet():
                print("❌ Фокус ушел из Comet после клика!")
                print("🔄 Возвращаю фокус...")
                if not force_comet_focus():
                    print("❌ Не удалось вернуть фокус")
                    continue
                time.sleep(1)
            
            # Шаг 7: Ввод текста
            print("📍 Шаг 7: Ввод текста...")
            test_text = f"LOCK_TEST_{attempt}"
            
            # Проверка фокуса ПЕРЕД вводом
            if not verify_focus_in_comet():
                print("❌ Фокус не в Comet перед вводом!")
                continue
            
            # Очищаем поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # Проверка фокуса ПОСЛЕ очистки
            if not verify_focus_in_comet():
                print("❌ Фокус ушел после очистки!")
                continue
            
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Проверка фокуса ПЕРЕД вводом текста
            if not verify_focus_in_comet():
                print("❌ Фокус не в Comet перед вводом текста!")
                continue
            
            # Ввод текста с проверками
            for i, char in enumerate(test_text):
                if not verify_focus_in_comet():
                    print(f"❌ Фокус ушел на символе {i+1}!")
                    break
                pyautogui.typewrite(char, interval=0.05)
                time.sleep(0.05)
            
            time.sleep(1)
            
            # Шаг 8: Финальная проверка
            print("📍 Шаг 8: Финальная проверка...")
            if not verify_focus_in_comet():
                print("❌ Фокус ушел после ввода!")
                continue
            
            # Получаем текст
            try:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                clipboard_content = pyperclip.paste()
                
                if test_text in clipboard_content:
                    print(f"🎉 УСПЕХ НА ПОПЫТКЕ #{attempt}!")
                    print(f"✅ Текст '{test_text}' введен в Comet!")
                    print(f"📋 Содержимое: {clipboard_content}")
                    
                    # Очищаем
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
                    
                    print("="*60)
                    print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                    print("✅ Фокус в Comet работает с блокировкой!")
                    print("="*60)
                    return True
                else:
                    print(f"❌ Текст не найден")
                    print(f"📝 Ожидали: {test_text}")
                    print(f"📝 Получили: {clipboard_content}")
                    
            except Exception as e:
                print(f"❌ Ошибка проверки: {e}")
            
            # Очищаем перед следующей попыткой
            try:
                if verify_focus_in_comet():
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
            except:
                pass
            
            print("💤 Жду 3 секунды...")
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Ошибка в попытке #{attempt}: {e}")
            time.sleep(3)
    
    print(f"\n❌ ВСЕ ПОПЫТКИ ИСЧЕРПАНЫ!")
    print("❌ ЗАДАЧА НЕ ВЫПОЛНЕНА!")
    return False

if __name__ == "__main__":
    print("🔒 ЗАПУСК ТЕСТА С БЛОКИРОВКОЙ ФОКУСА")
    print("🎯 Фокус будет заблокирован в Comet")
    print("⚠️ НЕ ПЕРЕКЛЮЧАЙТЕСЬ В ДРУГИЕ ОКНА!")
    print("❌ НЕ ОТКРЫВАЙТЕ IDE ВО ВРЕМЯ ТЕСТА!")
    print()
    
    print("⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ:")
    print("   1. Закройте все остальные окна")
    print("   2. Не переключайтесь в IDE")
    print("   3. Не трогайте мышь/клавиатуру")
    print("   4. Программа сама заблокирует фокус в Comet")
    print()
    
    input("Нажмите Enter когда готовы...")
    
    success = lock_focus_test()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Фокус в Comet работает с блокировкой!")
        print("🚀 Можно переходить к обработке доменов!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Нужно решать проблемы с переключением фокуса")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
