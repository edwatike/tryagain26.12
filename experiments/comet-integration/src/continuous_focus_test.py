"""
Непрерывный тест фокуса до получения положительного результата.
Не останавливается пока не получит успех!
"""
import time
import pyautogui
import subprocess
from pathlib import Path

def continuous_focus_test():
    print("🚀 НЕПРЕРЫВНЫЙ ТЕСТ ФОКУСА (ДО УСПЕХА)")
    print("="*60)
    print("🎯 Буду тестировать пока не получу положительный результат!")
    print("❌ Задача считается невыполненной пока не будет успех!")
    print("="*60)
    
    attempt = 0
    max_attempts = 100  # Максимум попыток
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n{'='*60}")
        print(f"🔄 ПОПЫТКА #{attempt}")
        print(f"{'='*60}")
        
        try:
            # Шаг 1: Проверить что Comet открыт
            print("📍 Шаг 1: Проверка Comet...")
            
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
                    print(f"✅ Найдено окно: {window.title}")
                    
                    # Активируем окно
                    try:
                        window.activate()
                        time.sleep(1)
                        print("✅ Окно активировано")
                    except:
                        print("⚠️ Не удалось активировать через pygetwindow")
                        # Пробуем альтернативный метод
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(1)
                        print("✅ Попробовал активировать через Alt+Tab")
                else:
                    print("❌ Окна Comet не найдены, открываю...")
                    # Открываем Comet
                    comet_paths = [
                        Path(r"C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
                        Path(r"C:\Program Files\Comet\Comet.exe"),
                        Path(r"C:\Program Files (x86)\Comet\Comet.exe"),
                        Path(r"C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe"),
                        Path(r"C:\Users\admin\AppData\Local\Comet\Application\Comet.exe")
                    ]
                    
                    for path in comet_paths:
                        if path.exists():
                            subprocess.Popen([str(path)], shell=True)
                            print(f"🚀 Comet запущен: {path}")
                            time.sleep(5)
                            break
                
            except ImportError:
                print("⚠️ pygetwindow недоступен")
            
            # Шаг 2: Открыть ассистента
            print("📍 Шаг 2: Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 3: Клик по полю ввода
            print("📍 Шаг 3: Клик по полю ввода...")
            screen_width, screen_height = pyautogui.size()
            assistant_panel_x = int(screen_width * 0.8)
            assistant_input_y = int(screen_height * 0.92)
            
            pyautogui.click(assistant_panel_x, assistant_input_y)
            time.sleep(0.5)
            
            # Шаг 4: Ввод тестового текста
            print("📍 Шаг 4: Ввод тестового текста...")
            test_text = f"FOCUS_TEST_{attempt}"
            pyautogui.typewrite(test_text, interval=0.05)
            time.sleep(0.5)
            
            print(f"✅ Текст '{test_text}' введен!")
            
            # Шаг 5: Проверка результата
            print(f"\n🤔 ПРОВЕРКА РЕЗУЛЬТАТА ПОПЫТКИ #{attempt}:")
            print(f"Появился ли текст '{test_text}' в поле ввода ассистента?")
            print("1. Да, текст появился - УСПЕХ!")
            print("2. Нет, текст не появился")
            print("3. Выйти из теста")
            
            try:
                answer = input("Ваш ответ (1-3): ").strip()
                
                if answer == "1":
                    print(f"\n🎉🎉🎉 УСПЕХ НА ПОПЫТКЕ #{attempt}! 🎉🎉🎉")
                    print(f"✅ Текст '{test_text}' появился в поле ввода!")
                    print("="*60)
                    print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                    print("✅ Фокус работает!")
                    print("="*60)
                    return True
                    
                elif answer == "2":
                    print(f"❌ Попытка #{attempt} не удалась")
                    print("💤 Жду 2 секунды перед следующей попыткой...")
                    time.sleep(2)
                    continue
                    
                elif answer == "3":
                    print("⚠️ Тест прерван пользователем")
                    return False
                    
                else:
                    print("❓ Неизвестный ответ, считаю как неудачу")
                    time.sleep(2)
                    continue
                    
            except Exception as e:
                print(f"❌ Ошибка получения ответа: {e}")
                time.sleep(2)
                continue
                
        except Exception as e:
            print(f"❌ Критическая ошибка в попытке #{attempt}: {e}")
            print("💤 Жду 3 секунды перед следующей попыткой...")
            time.sleep(3)
            continue
    
    print(f"\n❌ ВСЕ {max_attempts} ПОПЫТОК ИСЧЕРПАНЫ!")
    print("❌ ЗАДАЧА НЕ ВЫПОЛНЕНА!")
    print("💡 Нужно настраивать систему фокуса")
    return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК НЕПРЕРЫВНОГО ТЕСТА ФОКУСА")
    print("⚠️ НЕ ПРЕРЫВАТЬ ДО ПОЛУЧЕНИЯ РЕЗУЛЬТАТА!")
    print("⚠️ ЗАДАЧА СЧИТАЕТСЯ НЕВЫПОЛНЕННОЙ ДО УСПЕХА!")
    print()
    
    success = continuous_focus_test()
    
    if success:
        print("\n🎉 МИССИЯ ВЫПОЛНЕНА!")
        print("✅ Фокус в Comet работает!")
        print("🚀 Можно переходить к обработке доменов!")
    else:
        print("\n❌ МИССИЯ ПРОВАЛЕНА!")
        print("💡 Нужно решать проблемы с фокусом")
    
    print("\nНажмите Enter для выхода...")
    try:
        input()
    except:
        pass
