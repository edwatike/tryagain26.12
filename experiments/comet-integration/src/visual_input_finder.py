"""
Визуальный поиск поля ввода ассистента.
Рисует точки в разных местах чтобы найти поле ввода.
"""
import time
import pyautogui
import subprocess
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

def visual_input_finder():
    """Визуальный поиск поля ввода."""
    print("👁️ ВИЗУАЛЬНЫЙ ПОИСК ПОЛЯ ВВОДА")
    print("="*60)
    print("🎯 Буду рисовать точки в разных местах")
    print("👀 Вы увидите где кликает программа")
    print("✅ Когда точка попадет в поле ввода - текст будет вводиться туда")
    print("="*60)
    
    screen_width, screen_height = pyautogui.size()
    print(f"📐 Размер экрана: {screen_width}x{screen_height}")
    
    # Сетка точек для поиска
    grid_points = []
    
    # Правая панель (где должен быть ассистент)
    right_panel_x_start = int(screen_width * 0.6)  # 60% ширины
    right_panel_x_end = screen_width - 50         # 50px от края
    
    # Нижняя часть экрана (где поле ввода)
    input_y_start = int(screen_height * 0.7)      # 70% высоты
    input_y_end = screen_height - 50              # 50px от края
    
    # Создаем сетку 5x4
    for i in range(5):
        x = right_panel_x_start + (right_panel_x_end - right_panel_x_start) * i // 4
        for j in range(4):
            y = input_y_start + (input_y_end - input_y_start) * j // 3
            grid_points.append((x, y))
    
    print(f"🎯 Буду тестировать {len(grid_points)} точек")
    
    for idx, (x, y) in enumerate(grid_points):
        print(f"\n{'='*60}")
        print(f"🎯 ТОЧКА #{idx + 1}/{len(grid_points)}")
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
            
            # Шаг 3: Визуальный клик по точке
            print("📍 Шаг 3: Визуальный клик по точке...")
            print(f"   👁️ Смотрите на точку ({x}, {y})")
            
            # Двигаем курсор к точке (чтобы было видно)
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.5)
            
            # Кликаем
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            # Шаг 4: Тест ввода
            print("📍 Шаг 4: Тест ввода...")
            test_text = f"POINT_{idx + 1}"
            
            # Быстрая очистка и ввод
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)
            pyautogui.typewrite(test_text, interval=0.02)
            time.sleep(0.5)
            
            # Шаг 5: Проверка где появился текст
            print("📍 Шаг 5: Проверка результата...")
            print(f"   📝 Введен текст: {test_text}")
            print(f"   👀 Посмотрите где появился текст:")
            print(f"      1. В поле ввода ассистента (низ справа)")
            print(f"      2. В поле поиска (вверху)")
            print(f"      3. В другом месте")
            print(f"      4. Ни где не появился")
            
            try:
                answer = input("Где появился текст (1-4): ").strip()
                
                if answer == "1":
                    print(f"🎉 НАЙДЕНО! ТОЧКА #{idx + 1} РАБОТАЕТ!")
                    print(f"✅ Координаты поля ввода: ({x}, {y})")
                    print(f"📝 Текст '{test_text}' введен в поле ассистента!")
                    
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
                    
                elif answer == "2":
                    print("❌ Текст в поле поиска - не то место")
                elif answer == "3":
                    print("❌ Текст в другом месте")
                elif answer == "4":
                    print("❌ Текст не появился")
                else:
                    print("❓ Неизвестный ответ")
                
            except Exception as e:
                print(f"❌ Ошибка ввода ответа: {e}")
            
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
    print("❌ ПОЛЕ ВВОДА НЕ НАЙДЕНО!")
    return False, None

if __name__ == "__main__":
    print("👁️ ЗАПУСК ВИЗУАЛЬНОГО ПОИСКА ПОЛЯ ВВОДА")
    print("🎯 Программа будет рисовать точки в разных местах")
    print("👀 Вы должны видеть где кликает курсор")
    print("✅ Когда точка попадет в поле ввода - текст будет вводиться туда")
    print()
    
    print("⚠️ ВАЖНО:")
    print("   1. Смотрите на экран")
    print("   2. Следите где появляется курсор")
    print("   3. Отвечайте куда вводится текст")
    print()
    
    input("Нажмите Enter когда готовы...")
    
    success, coordinates = visual_input_finder()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Найдены координаты поля ввода ассистента!")
        print(f"🎯 Координаты: {coordinates}")
        print("🚀 Можно использовать в основной программе!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Поле ввода не найдено в проверенных областях")
        print("🔍 Возможно ассистент имеет другую структуру")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
