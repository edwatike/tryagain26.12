"""
Автоматический тест фокуса без ожидания пользовательского ввода.
Запускается сразу и проверяет фокус в цикле до успеха.
"""
import asyncio
import sys
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка зависимостей
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.error("pyautogui не установлен!")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


class AutoTestFocus:
    """Автоматический тест фокуса с повторными попытками."""
    
    def __init__(self):
        logger.info("AutoTestFocus инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        self.max_attempts = 5
        self.attempt_delay = 3
    
    def open_comet_automatically(self, debug: bool = False) -> bool:
        """Автоматически открыть Comet браузер."""
        try:
            if debug:
                logger.info("🚀 Автоматическое открытие Comet...")
            
            # Пути к Comet
            comet_paths = [
                Path(r"C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
                Path(r"C:\Program Files\Comet\Comet.exe"),
                Path(r"C:\Program Files (x86)\Comet\Comet.exe"),
                Path(r"C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe"),
                Path(r"C:\Users\admin\AppData\Local\Comet\Application\Comet.exe")
            ]
            
            comet_executable = None
            for path in comet_paths:
                if path.exists():
                    comet_executable = str(path)
                    if debug:
                        logger.info(f"📁 Найден Comet: {comet_executable}")
                    break
            
            if not comet_executable:
                if debug:
                    logger.error("❌ Comet не найден в стандартных местах")
                print("❌ Comet не найден! Установите Comet браузер")
                return False
            
            # Запускаем Comet
            if debug:
                logger.info(f"🚀 Запускаю: {comet_executable}")
            
            subprocess.Popen([comet_executable], shell=True)
            
            # Ждем запуска
            if debug:
                logger.info("⏳ Жду запуска Comet (5 секунд)...")
            time.sleep(5)
            
            # Проверяем что окно появилось
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if not windows:
                    all_windows = gw.getAllWindows()
                    for win in all_windows:
                        if 'comet' in win.title.lower():
                            windows = [win]
                            break
                
                if windows:
                    window = windows[0]
                    if debug:
                        logger.info(f"✅ Comet открыт: {window.title}")
                    
                    try:
                        window.activate()
                        time.sleep(1)
                        
                        if window.isActive:
                            if debug:
                                logger.info("✅ Окно Comet активно")
                            return True
                        else:
                            if debug:
                                logger.warning("⚠️ Окно не стало активным")
                            return False
                    except Exception as e:
                        if debug:
                            logger.error(f"❌ Ошибка активации: {e}")
                        return False
                else:
                    if debug:
                        logger.error("❌ Окно Comet не появилось после запуска")
                    return False
            else:
                if debug:
                    logger.info("⏳ Дополнительное ожидание (без проверки окна)...")
                time.sleep(3)
                return True
                
        except Exception as e:
            if debug:
                logger.error(f"❌ Ошибка открытия Comet: {e}")
            return False
    
    def ensure_window_focused(self, debug: bool = False) -> bool:
        """Убедиться что окно Comet активно. Если не открыто - открыть автоматически."""
        try:
            if debug:
                logger.info("🔍 Проверка активного окна...")
            
            # Проверяем есть ли окна Comet
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if not windows:
                    all_windows = gw.getAllWindows()
                    for win in all_windows:
                        if 'comet' in win.title.lower():
                            windows = [win]
                            break
                
                if windows:
                    window = windows[0]
                    if debug:
                        logger.info(f"📁 Найдено окно: {window.title}")
                    
                    # Пробуем несколько методов активации
                    activation_methods = [
                        ("pygetwindow.activate()", lambda: self._activate_via_getwindow(window)),
                        ("Alt+Tab", lambda: self._activate_via_alt_tab()),
                        ("PowerShell SetForegroundWindow", lambda: self._activate_via_powershell(window)),
                        ("Клик по центру", lambda: self._activate_via_click(window))
                    ]
                    
                    for method_name, method_func in activation_methods:
                        try:
                            if debug:
                                logger.info(f"🔄 Пробую активацию через {method_name}...")
                            
                            success = method_func()
                            if success:
                                if debug:
                                    logger.info(f"✅ Активация через {method_name} успешна")
                                return True
                            else:
                                if debug:
                                    logger.warning(f"⚠️ Активация через {method_name} не удалась")
                                continue
                                
                        except Exception as e:
                            if debug:
                                logger.warning(f"⚠️ Ошибка активации через {method_name}: {e}")
                            continue
                    
                    # Если все методы не сработали
                    if debug:
                        logger.error("❌ Все методы активации не сработали")
                    return False
                else:
                    # Окна не найдены - открываем Comet автоматически
                    if debug:
                        logger.info("🚀 Comet не найден, открываю автоматически...")
                    return self.open_comet_automatically(debug=debug)
            else:
                if debug:
                    logger.warning("⚠️ pygetwindow недоступен, пробую открыть Comet")
                return self.open_comet_automatically(debug=debug)
                
        except Exception as e:
            if debug:
                logger.error(f"❌ Ошибка проверки окна: {e}")
            return False
    
    def _activate_via_getwindow(self, window) -> bool:
        """Активация через pygetwindow."""
        try:
            window.activate()
            time.sleep(0.5)
            return window.isActive
        except:
            return False
    
    def _activate_via_alt_tab(self) -> bool:
        """Активация через Alt+Tab."""
        try:
            # Alt+Tab для переключения на последнее окно
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            return True
        except:
            return False
    
    def _activate_via_powershell(self, window) -> bool:
        """Активация через PowerShell."""
        try:
            import subprocess
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
            time.sleep(1)
            return True
        except:
            return False
    
    def _activate_via_click(self, window) -> bool:
        """Активация через клик по центру окна."""
        try:
            if hasattr(window, 'left') and hasattr(window, 'top') and hasattr(window, 'width') and hasattr(window, 'height'):
                center_x = window.left + window.width // 2
                center_y = window.top + window.height // 2
                
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                return True
            else:
                # Если нет координат, кликаем в центр экрана
                screen_width, screen_height = pyautogui.size()
                center_x = screen_width // 2
                center_y = screen_height // 2
                
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                return True
        except:
            return False
    
    def click_assistant_input_field(self, debug: bool = False) -> bool:
        """Гарантированно ставит фокус в поле ввода ассистента."""
        try:
            if not PYAUTOGUI_AVAILABLE:
                logger.error("❌ pyautogui недоступен!")
                return False
            
            if debug:
                logger.info("🎯 Установка фокуса в поле ввода ассистента...")
            
            # Пауза чтобы ассистент успел отрисоваться
            time.sleep(0.8)
            
            # Определяем координаты поля ввода ассистента
            assistant_panel_x = int(self.screen_width * 0.8)   # 80% ширины
            assistant_input_y = int(self.screen_height * 0.92)  # 92% высоты
            
            if debug:
                logger.info(f"📍 Клик по input ассистента: ({assistant_panel_x}, {assistant_input_y})")
            
            # Выполняем клик
            pyautogui.click(assistant_panel_x, assistant_input_y)
            time.sleep(0.3)
            
            if debug:
                logger.info("✅ Клик по полю ввода выполнен")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка клика по полю ввода: {e}")
            return False
    
    async def send_prompt_with_focus(self, prompt: str, debug: bool = False) -> bool:
        """Отправить промпт с гарантированным фокусом."""
        try:
            if debug:
                logger.info("🚀 Начинаю отправку промпта с гарантированным фокусом...")
            
            # 1. Убедиться, что окно Comet активно
            if debug:
                logger.info("📍 Шаг 1: Активация окна Comet...")
            window_ok = self.ensure_window_focused(debug=debug)
            if not window_ok:
                logger.error("❌ Не удалось активировать окно Comet")
                return False
            
            # 2. Открыть ассистента
            if debug:
                logger.info("📍 Шаг 2: Открытие ассистента (Alt+A)...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(1.5)
            
            if debug:
                logger.info("✅ Alt+A отправлен")
            
            # 3. Поставить фокус в поле ввода ассистента
            if debug:
                logger.info("📍 Шаг 3: Установка фокуса в поле ввода...")
            focus_ok = self.click_assistant_input_field(debug=debug)
            if not focus_ok:
                logger.error("❌ Не удалось установить фокус в поле ввода")
                return False
            
            time.sleep(0.3)
            
            # 4. Ввести текст промпта
            if debug:
                logger.info("📍 Шаг 4: Ввод текста промпта...")
            pyautogui.typewrite(prompt, interval=0.03)
            time.sleep(0.3)
            
            if debug:
                logger.info("✅ Текст промпта введен")
            
            # 5. Нажать Enter
            if debug:
                logger.info("📍 Шаг 5: Отправка промпта (Enter)...")
            pyautogui.press('enter')
            
            if debug:
                logger.info("✅ Enter отправлен")
                logger.info("🎉 Промпт отправлен с гарантированным фокусом!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    async def run_single_test(self, attempt: int) -> bool:
        """Запустить один тестовый прогон."""
        print(f"\n🧪 ПОПЫТКА #{attempt}")
        print("="*50)
        
        try:
            # Шаг 1: Убедимся что Comet открыт
            print("📍 Шаг 1: Проверка/открытие Comet...")
            comet_ok = self.ensure_window_focused(debug=True)
            if not comet_ok:
                print("❌ Не удалось открыть/активировать Comet")
                return False
            
            # Шаг 2: Переход на тестовую страницу
            print("📍 Шаг 2: Переход на тестовую страницу...")
            test_url = "https://google.com"
            
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.5)
            
            pyautogui.typewrite(test_url, interval=0.05)
            time.sleep(0.5)
            
            pyautogui.press('enter')
            time.sleep(3)
            
            print("✅ Страница загружена")
            
            # Шаг 3: Отправляем тестовый промпт
            test_prompt = "FOCUS_TEST_123"
            print(f"📍 Шаг 3: Отправка тестового промпта '{test_prompt}'...")
            
            success = await self.send_prompt_with_focus(test_prompt, debug=True)
            
            if not success:
                print("❌ Ошибка отправки тестового промпта")
                return False
            
            # Шаг 4: Проверка результата
            print(f"\n🤔 Проверка результата попытки #{attempt}:")
            print("Появился ли текст 'FOCUS_TEST_123' в ассистенте?")
            print("1. Да, текст появился")
            print("2. Нет, текст не появился")
            
            try:
                import builtins
                answer = builtins.input("Ваш ответ (1-2): ").strip()
                
                if answer == "1":
                    print("🎉 ПОПЫТКА УСПЕШНА!")
                    logger.info(f"✅ Тест фокуса УСПЕШЕН на попытке #{attempt}")
                    return True
                elif answer == "2":
                    print("❌ Попытка не удалась")
                    logger.info(f"❌ Тест фокуса ПРОВАЛЕН на попытке #{attempt}")
                    return False
                else:
                    print("❓ Неизвестный ответ, считаю как неудачу")
                    return False
                    
            except Exception as e:
                logger.error(f"Ошибка получения ответа: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка теста: {e}")
            print(f"❌ Критическая ошибка: {e}")
            return False
    
    async def run_tests_until_success(self) -> bool:
        """Запускать тесты до получения положительного результата."""
        print("🚀 АВТОМАТИЧЕСКИЙ ТЕСТ ФОКУСА (ДО УСПЕХА)")
        print("="*60)
        print("🎯 Буду запускать тесты пока не получу положительный результат")
        print(f"🔄 Максимум попыток: {self.max_attempts}")
        print(f"⏱️ Задержка между попытками: {self.attempt_delay} секунд")
        print("="*60)
        
        for attempt in range(1, self.max_attempts + 1):
            print(f"\n{'='*60}")
            print(f"🔄 НАЧАЛО ПОПЫТКИ #{attempt} ИЗ {self.max_attempts}")
            print(f"{'='*60}")
            
            success = await self.run_single_test(attempt)
            
            if success:
                print(f"\n🎉 УСПЕХ! Тест пройден на попытке #{attempt}")
                print("="*60)
                return True
            else:
                if attempt < self.max_attempts:
                    print(f"\n⏳ Попытка #{attempt} не удалась")
                    print(f"💤 Жду {self.attempt_delay} секунд перед следующей попыткой...")
                    time.sleep(self.attempt_delay)
                else:
                    print(f"\n❌ ВСЕ ПОПЫТКИ ИСЧЕРПАНЫ!")
                    print(f"🔄 Максимум попыток: {self.max_attempts}")
                    print("="*60)
                    return False
        
        return False


async def main():
    """Главная функция."""
    tester = AutoTestFocus()
    
    print("🤖 АВТОМАТИЧЕСКИЙ ТЕСТ ФОКУСА")
    print("="*60)
    print("🎯 Цель: проверить что текст появляется в ассистенте")
    print("📝 Тестовый текст: FOCUS_TEST_123")
    print("🔄 Буду повторять до успеха!")
    print("="*60)
    
    print(f"\n⚠️ ВАЖНО:")
    print("   ✅ Не трогайте мышь/клавиатуру во время тестов")
    print("   ✅ Программа сделает все автоматически")
    print("   ✅ Буду спрашивать результат после каждой попытки")
    
    print(f"\n🚀 Начинаю автоматические тесты...")
    time.sleep(2)
    
    success = await tester.run_tests_until_success()
    
    if success:
        print("\n🎉 ОТЛИЧНО! Фокус работает!")
        print("✅ Можно переходить к обработке доменов")
    else:
        print("\n❌ РЕЗУЛЬТАТ:")
        print("❌ Не удалось добиться успешного ввода текста")
        print("💡 Возможные проблемы:")
        print("   - Неверные координаты клика")
        print("   - Проблемы с ассистентом Comet")
        print("   - Тайминги не подходят")
    
    print("\nНажмите Enter для выхода...")
    try:
        import builtins
        builtins.input()
    except:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
