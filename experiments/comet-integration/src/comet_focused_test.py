"""
Тест который гарантированно работает только с окном Comet.
Сначала проверяет что фокус именно в Comet, потом выполняет действия.
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

def ensure_comet_is_active():
    """Гарантированно сделать Comet активным окном."""
    print("🎯 ГАРАНТИРОВАННАЯ АКТИВАЦИЯ COMET")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        print(f"   🔄 Попытка {attempt + 1}/{max_attempts}")
        
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
                print(f"   📁 Найдено: {window.title}")
                
                # Метод 1: pygetwindow.activate()
                try:
                    window.activate()
                    time.sleep(1)
                    active_title = get_active_window_title()
                    if 'comet' in active_title.lower():
                        print(f"   ✅ Активировано через pygetwindow: {active_title}")
                        return True
                except Exception as e:
                    print(f"   ❌ pygetwindow.activate() не сработал: {e}")
                
                # Метод 2: PowerShell SetForegroundWindow
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
                    active_title = get_active_window_title()
                    if 'comet' in active_title.lower():
                        print(f"   ✅ Активировано через PowerShell: {active_title}")
                        return True
                except Exception as e:
                    print(f"   ❌ PowerShell не сработал: {e}")
                
                # Метод 3: Клик по окну
                try:
                    if hasattr(window, 'left') and hasattr(window, 'top'):
                        center_x = window.left + window.width // 2
                        center_y = window.top + window.height // 2
                        pyautogui.click(center_x, center_y)
                        time.sleep(1)
                        active_title = get_active_window_title()
                        if 'comet' in active_title.lower():
                            print(f"   ✅ Активировано через клик: {active_title}")
                            return True
                except Exception as e:
                    print(f"   ❌ Клик не сработал: {e}")
                
                # Метод 4: Alt+Tab цикл
                try:
                    # Несколько раз Alt+Tab чтобы дойти до Comet
                    for i in range(5):
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(0.5)
                        active_title = get_active_window_title()
                        if 'comet' in active_title.lower():
                            print(f"   ✅ Активировано через Alt+Tab: {active_title}")
                            return True
                except Exception as e:
                    print(f"   ❌ Alt+Tab не сработал: {e}")
                
            else:
                print("   ❌ Окна Comet не найдены")
                
        except Exception as e:
            print(f"   ❌ Ошибка активации: {e}")
        
        time.sleep(1)
    
    print("   ❌ Не удалось активировать Comet")
    return False

def verify_comet_active():
    """Проверить что Comet действительно активен."""
    print("🔍 ПРОВЕРКА АКТИВНОГО ОКНА")
    
    active_title = get_active_window_title()
    print(f"   📝 Активное окно: {active_title}")
    
    if 'comet' in active_title.lower():
        print("   ✅ Comet активен!")
        return True
    else:
        print("   ❌ Comet не активен!")
        return False

def test_comet_focus():
    """Тест фокуса только в окне Comet."""
    print("🚀 ТЕСТ ФОКУСА ТОЛЬКО В COMET")
    print("="*60)
    print("🎯 Гарантированная работа только с окном Comet")
    print("❌ Никаких действий в других окнах!")
    print("="*60)
    
    attempt = 0
    max_attempts = 20
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"🔄 ПОПЫТКА #{attempt}")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Гарантированная активация Comet
            print("📍 Шаг 1: Гарантированная активация Comet...")
            if not ensure_comet_is_active():
                print("❌ Не удалось активировать Comet")
                time.sleep(2)
                continue
            
            # Шаг 2: Проверка что Comet действительно активен
            print("📍 Шаг 2: Проверка активности...")
            if not verify_comet_active():
                print("❌ Comet не активен после активации")
                time.sleep(2)
                continue
            
            # Шаг 3: Открыть ассистента (только в Comet!)
            print("📍 Шаг 3: Alt+A в Comet...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 4: Проверить что ассистент открылся в Comet
            print("📍 Шаг 4: Проверка ассистента...")
            if not verify_comet_active():
                print("❌ Ассистент открылся не в Comet")
                time.sleep(2)
                continue
            
            # Шаг 5: Клик по полю ввода в Comet
            print("📍 Шаг 5: Клик по полю ввода в Comet...")
            screen_width, screen_height = pyautogui.size()
            assistant_panel_x = int(screen_width * 0.8)
            assistant_input_y = int(screen_height * 0.92)
            
            pyautogui.click(assistant_panel_x, assistant_input_y)
            time.sleep(0.5)
            
            # Шаг 6: Проверить что фокус в Comet
            print("📍 Шаг 6: Проверка фокуса после клика...")
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet после клика")
                time.sleep(2)
                continue
            
            # Шаг 7: Ввод текста только в Comet
            print("📍 Шаг 7: Ввод текста в Comet...")
            test_text = f"COMET_TEST_{attempt}"
            
            # Сначала очищаем поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Вводим текст
            pyautogui.typewrite(test_text, interval=0.05)
            time.sleep(1)
            
            # Шаг 8: Проверить что текст введен в Comet
            print("📍 Шаг 8: Проверка текста в Comet...")
            if not verify_comet_active():
                print("❌ Фокус ушел из Comet при вводе")
                time.sleep(2)
                continue
            
            # Получаем текст из поля ввода
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
                    
                    # Очищаем поле
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
                    
                    print("="*60)
                    print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                    print("✅ Фокус в Comet работает!")
                    print("="*60)
                    return True
                else:
                    print(f"❌ Текст не найден в поле ввода")
                    print(f"📝 Ожидали: {test_text}")
                    print(f"📝 Получили: {clipboard_content}")
                    
            except Exception as e:
                print(f"❌ Ошибка проверки текста: {e}")
            
            # Очищаем перед следующей попыткой
            try:
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.press('delete')
                time.sleep(0.5)
            except:
                pass
            
            print("💤 Жду 2 секунды...")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Ошибка в попытке #{attempt}: {e}")
            time.sleep(3)
    
    print(f"\n❌ ВСЕ ПОПЫТКИ ИСЧЕРПАНЫ!")
    print("❌ ЗАДАЧА НЕ ВЫПОЛНЕНА!")
    return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТА ФОКУСА ТОЛЬКО В COMET")
    print("🎯 Гарантированная работа только с окном Comet")
    print("❌ Никаких действий в других окнах!")
    print()
    
    success = test_comet_focus()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Фокус в Comet работает!")
        print("🚀 Можно переходить к обработке доменов!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Нужно решать проблемы с фокусом в Comet")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
