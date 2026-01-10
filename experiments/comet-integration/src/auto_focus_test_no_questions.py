"""
Автоматический тест фокуса с самопроверкой результатов.
Без вопросов пользователю - программа сама проверяет успех!
"""
import time
import pyautogui
import subprocess
import pyperclip
from pathlib import Path
import re

def check_text_in_clipboard(expected_text: str) -> bool:
    """Проверить есть ли ожидаемый текст в буфере обмена."""
    try:
        clipboard_content = pyperclip.paste()
        return expected_text in clipboard_content
    except:
        return False

def check_text_on_screen(expected_text: str) -> bool:
    """Проверить есть ли текст на экране через pyautogui."""
    try:
        # Ищем текст на экране
        text_locations = pyautogui.locateAllOnScreen(expected_text, confidence=0.8)
        return len(list(text_locations)) > 0
    except:
        return False

def get_assistant_text() -> str:
    """Получить текст из поля ввода ассистента."""
    try:
        # Выделяем все текст в поле ввода
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        # Копируем в буфер обмена
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        # Получаем из буфера обмена
        clipboard_content = pyperclip.paste()
        
        # Возвращаем курсор в конец
        pyautogui.press('end')
        time.sleep(0.5)
        
        return clipboard_content
    except:
        return ""

def clear_assistant_field():
    """Очистить поле ввода ассистента."""
    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        pyautogui.press('delete')
        time.sleep(0.5)
    except:
        pass

def auto_focus_test():
    print("🚀 АВТОМАТИЧЕСКИЙ ТЕСТ ФОКУСА (САМОПРОВЕРКА)")
    print("="*60)
    print("🎯 Программа сама проверит результаты!")
    print("❌ Без вопросов пользователю!")
    print("✅ Полная автоматизация!")
    print("="*60)
    
    attempt = 0
    max_attempts = 50
    
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
                        print("⚠️ Активация через pygetwindow не удалась")
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(1)
                        print("✅ Попробовал Alt+Tab")
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
            
            # Шаг 2: Очистить поле ввода
            print("📍 Шаг 2: Очистка поля ввода...")
            clear_assistant_field()
            
            # Шаг 3: Открыть ассистента
            print("📍 Шаг 3: Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 4: Клик по полю ввода
            print("📍 Шаг 4: Клик по полю ввода...")
            screen_width, screen_height = pyautogui.size()
            assistant_panel_x = int(screen_width * 0.8)
            assistant_input_y = int(screen_height * 0.92)
            
            pyautogui.click(assistant_panel_x, assistant_input_y)
            time.sleep(0.5)
            
            # Шаг 5: Ввод тестового текста
            print("📍 Шаг 5: Ввод тестового текста...")
            test_text = f"FOCUS_TEST_{attempt}"
            pyautogui.typewrite(test_text, interval=0.05)
            time.sleep(1)
            
            print(f"✅ Текст '{test_text}' введен!")
            
            # Шаг 6: АВТОМАТИЧЕСКАЯ ПРОВЕРКА РЕЗУЛЬТАТА
            print("📍 Шаг 6: Автоматическая проверка результата...")
            
            # Метод 1: Проверка через буфер обмена
            print("   🔍 Метод 1: Проверка через буфер обмена...")
            assistant_text = get_assistant_text()
            clipboard_success = test_text in assistant_text
            
            if clipboard_success:
                print(f"   ✅ Текст найден в буфере обмена!")
            else:
                print(f"   ❌ Текст не найден в буфере обмена")
                print(f"   📝 Содержимое поля: '{assistant_text[:100]}...'")
            
            # Метод 2: Проверка через скриншот (если доступно)
            print("   🔍 Метод 2: Проверка через скриншот...")
            try:
                # Делаем скриншот области поля ввода
                screen_width, screen_height = pyautogui.size()
                input_region = (
                    int(screen_width * 0.6),  # левая граница правой панели
                    int(screen_height * 0.85), # верхняя граница поля ввода
                    int(screen_width * 0.4),  # ширина правой панели
                    int(screen_height * 0.15) # высота нижней части
                )
                
                screenshot = pyautogui.screenshot(region=input_region)
                # Здесь можно добавить OCR, но пока пропускаем
                screenshot_success = False  # Заглушка для OCR
                print("   ⚠️ OCR не реализован, пропускаем")
            except:
                screenshot_success = False
                print("   ❌ Скриншот не удался")
            
            # Метод 3: Проверка через выделение и поиск
            print("   🔍 Метод 3: Проверка через выделение...")
            try:
                # Выделяем весь текст и ищем наш тестовый текст
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                
                # Ищем текст через поиск в поле
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.5)
                pyautogui.typewrite(test_text, interval=0.05)
                time.sleep(1)
                
                # Проверяем найдено ли что-то
                pyautogui.press('escape')  # Закрываем поиск
                time.sleep(0.5)
                
                # Снова получаем текст для проверки
                final_text = get_assistant_text()
                search_success = test_text in final_text
                
                if search_success:
                    print(f"   ✅ Текст найден через поиск!")
                else:
                    print(f"   ❌ Текст не найден через поиск")
                
            except:
                search_success = False
                print("   ❌ Поиск не удался")
            
            # Общая оценка успеха
            total_success = clipboard_success or screenshot_success or search_success
            
            if total_success:
                print(f"\n🎉🎉🎉 УСПЕХ НА ПОПЫТКЕ #{attempt}! 🎉🎉🎉")
                print(f"✅ Текст '{test_text}' успешно введен!")
                print(f"📊 Результаты проверки:")
                print(f"   📋 Буфер обмена: {'✅' if clipboard_success else '❌'}")
                print(f"   📸 Скриншот: {'✅' if screenshot_success else '❌'}")
                print(f"   🔍 Поиск: {'✅' if search_success else '❌'}")
                print("="*60)
                print("🎯 ЗАДАЧА ВЫПОЛНЕНА!")
                print("✅ Фокус работает!")
                print("="*60)
                
                # Очищаем поле ввода после успеха
                clear_assistant_field()
                return True
                
            else:
                print(f"❌ Попытка #{attempt} не удалась")
                print(f"📊 Результаты проверки:")
                print(f"   📋 Буфер обмена: {'✅' if clipboard_success else '❌'}")
                print(f"   📸 Скриншот: {'✅' if screenshot_success else '❌'}")
                print(f"   🔍 Поиск: {'✅' if search_success else '❌'}")
                
                # Очищаем поле перед следующей попыткой
                clear_assistant_field()
                
                print("💤 Жду 2 секунды перед следующей попыткой...")
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
    print("🚀 ЗАПУСК АВТОМАТИЧЕСКОГО ТЕСТА ФОКУСА")
    print("🤖 Программа сама проверит результаты!")
    print("❌ Без вопросов пользователю!")
    print("⚠️ ЗАДАЧА СЧИТАЕТСЯ НЕВЫПОЛНЕННОЙ ДО УСПЕХА!")
    print()
    
    success = auto_focus_test()
    
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
