"""
ФИНАЛЬНОЕ РЕШЕНИЕ COMET
Открывает домен → передает промпт ассистенту → ждет результат → передает результат
"""
import asyncio
import sys
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


class FinalCometSolution:
    """Финальное решение для работы с Comet."""
    
    def __init__(self):
        logger.info("🚀 FinalCometSolution инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # РАБОЧИЕ КООРДИНАТЫ
        self.input_field_x = int(self.screen_width * 0.85)   # Поле ввода ассистента
        self.input_field_y = int(self.screen_height * 0.92)
        
        # АДРЕСНАЯ СТРОКА
        self.address_bar_x = int(self.screen_width * 0.5)   # Центр экрана
        self.address_bar_y = int(self.screen_height * 0.05) # 5% от верха
        
        logger.info(f"🎯 Поле ввода ассистента: ({self.input_field_x}, {self.input_field_y})")
        logger.info(f"🌐 Адресная строка: ({self.address_bar_x}, {self.address_bar_y})")
    
    def get_active_window_title(self):
        """Получить заголовок активного окна."""
        try:
            active = gw.getActiveWindow()
            return active.title if active else "Unknown"
        except:
            return "Error"
    
    def verify_comet_active(self):
        """Проверить что Comet активен."""
        active_title = self.get_active_window_title()
        is_comet = 'comet' in active_title.lower()
        logger.info(f"🔍 Активное окно: {active_title}")
        logger.info(f"✅ Comet активен: {is_comet}")
        return is_comet
    
    def force_activate_comet(self) -> bool:
        """Принудительно активировать Comet."""
        try:
            import subprocess
            
            logger.info("🔍 Поиск окон Comet...")
            windows = gw.getWindowsWithTitle('Comet')
            if not windows:
                all_windows = gw.getAllWindows()
                for win in all_windows:
                    if 'comet' in win.title.lower():
                        windows = [win]
                        break
            
            if not windows:
                logger.error("❌ Окна Comet не найдены!")
                return False
            
            window = windows[0]
            logger.info(f"📁 Найдено окно: {window.title}")
            
            # PowerShell активация
            logger.info("🔄 PowerShell SetForegroundWindow...")
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
            
            if self.verify_comet_active():
                logger.info("✅ Comet активирован успешно!")
                return True
            
            logger.error("❌ Не удалось активировать Comet")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка активации Comet: {e}")
            return False
    
    def open_domain_in_comet(self, domain: str) -> bool:
        """Открыть домен в Comet."""
        try:
            logger.info(f"🌐 Открытие домена в Comet: {domain}")
            url = f"https://{domain}"
            
            # Шаг 1: Активировать Comet
            if not self.force_activate_comet():
                logger.error("❌ Не удалось активировать Comet")
                return False
            
            # Шаг 2: Фокус на адресную строку
            logger.info("📍 Фокус на адресную строку...")
            
            # Пробуем несколько методов
            logger.info("   🔄 Ctrl+L...")
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1)
            
            logger.info("   🔄 Клик по адресу...")
            pyautogui.click(self.address_bar_x, self.address_bar_y)
            time.sleep(0.5)
            
            logger.info("   🔄 F6...")
            pyautogui.press('f6')
            time.sleep(0.5)
            
            # Шаг 3: Ввести URL
            logger.info(f"📍 Ввод URL: {url}")
            
            # Очистить
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Ввести URL
            pyautogui.typewrite(url, interval=0.05)
            time.sleep(0.5)
            
            # Шаг 4: Enter
            logger.info("📍 Enter - переход к странице...")
            pyautogui.press('enter')
            time.sleep(4)  # Ждем загрузки
            
            # Проверяем что Comet все еще активен
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после перехода")
                return False
            
            logger.info("✅ Домен открыт в Comet!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка открытия домена {domain}: {e}")
            return False
    
    def send_prompt_to_assistant(self, prompt: str) -> bool:
        """Отправить промпт ассистенту."""
        try:
            logger.info(f"🤖 Отправка промпта ассистенту: {prompt}")
            
            # Убедиться что Comet активен
            if not self.force_activate_comet():
                logger.error("❌ Не удалось активировать Comet")
                return False
            
            # Alt+A - открыть ассистента
            logger.info("📍 Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Клик по полю ввода
            logger.info(f"📍 Клик по полю ввода: ({self.input_field_x}, {self.input_field_y})")
            pyautogui.click(self.input_field_x, self.input_field_y)
            time.sleep(0.5)
            
            # Очистить поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Ввести промпт
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(0.5)
            
            # Enter
            logger.info("📍 Enter - отправка промпта...")
            pyautogui.press('enter')
            time.sleep(0.5)
            
            logger.info("✅ Промпт отправлен ассистенту!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    def wait_for_assistant_result(self, wait_time: int = 15) -> bool:
        """Ждать пока ассистент отработает."""
        try:
            logger.info(f"⏳ Ожидаю результат от ассистента {wait_time} секунд...")
            
            for i in range(wait_time):
                time.sleep(1)
                if (i + 1) % 5 == 0:  # Каждые 5 секунд
                    logger.info(f"   ⏳ Прошло {i + 1}/{wait_time} секунд...")
            
            logger.info("✅ Ожидание завершено!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка ожидания: {e}")
            return False
    
    def get_assistant_result(self) -> Dict[str, Any]:
        """Получить результат от ассистента."""
        try:
            logger.info("📥 Получение результата от ассистента...")
            
            # Убедиться что Comet активен
            if not self.force_activate_comet():
                return self._create_error_result("unknown", "Comet не активен")
            
            # Alt+A - убедиться что ассистент открыт
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Выделить весь текст в ассистенте
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # Скопировать в буфер обмена
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            # Получить из буфера обмена
            if PYPERCLIP_AVAILABLE:
                try:
                    clipboard_content = pyperclip.paste()
                    logger.info(f"📋 Получен текст из буфера обмена: {len(clipboard_content)} символов")
                    
                    # Парсим результат
                    return self._parse_assistant_response(clipboard_content)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка чтения буфера обмена: {e}")
                    return self._create_error_result("unknown", f"Ошибка буфера обмена: {e}")
            else:
                logger.error("❌ pyperclip недоступен")
                return self._create_error_result("unknown", "pyperclip недоступен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения результата: {e}")
            return self._create_error_result("unknown", f"Ошибка получения результата: {e}")
    
    def _parse_assistant_response(self, response_text: str) -> Dict[str, Any]:
        """Парсить ответ ассистента."""
        try:
            logger.info("🔍 Парсинг ответа ассистента...")
            
            # Ищем ИНН
            inn = None
            import re
            inn_pattern = r'\b\d{10}\b'
            inn_matches = re.findall(inn_pattern, response_text)
            if inn_matches:
                inn = inn_matches[0]
                logger.info(f"📋 Найден ИНН: {inn}")
            
            # Ищем email
            email = None
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, response_text)
            if email_matches:
                email = email_matches[0]
                logger.info(f"📋 Найден email: {email}")
            
            # Создаем результат
            result = {
                "success": True,
                "inn": inn,
                "email": email,
                "raw_response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Результат спарсен: ИНН={inn}, Email={email}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга: {e}")
            return self._create_error_result("unknown", f"Ошибка парсинга: {e}")
    
    def _create_error_result(self, domain: str, error: str) -> Dict[str, Any]:
        """Создать результат ошибки."""
        return {
            "domain": domain,
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    async def extract_domain_info(self, domain: str, wait_time: int = 15) -> Dict[str, Any]:
        """Полный цикл извлечения информации о домене."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 НАЧАЛО ИЗВЛЕЧЕНИЯ ДЛЯ {domain}")
            
            # Шаг 1: Открыть домен в Comet
            if not self.open_domain_in_comet(domain):
                return self._create_error_result(domain, "Не удалось открыть домен")
            
            # Шаг 2: Отправить промпт ассистенту
            prompt = "Найди ИНН и email для этого сайта"
            if not self.send_prompt_to_assistant(prompt):
                return self._create_error_result(domain, "Не удалось отправить промпт")
            
            # Шаг 3: Ждать пока ассистент отработает
            if not self.wait_for_assistant_result(wait_time):
                return self._create_error_result(domain, "Ошибка ожидания")
            
            # Шаг 4: Получить результат
            result = self.get_assistant_result()
            
            # Добавляем информацию о домене
            result["domain"] = domain
            result["execution_time"] = time.time() - start_time
            
            logger.info(f"✅ ИЗВЛЕЧЕНИЕ ЗАВЕРШЕНО за {result['execution_time']:.2f}с")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка извлечения для {domain}: {e}")
            return self._create_error_result(domain, f"Критическая ошибка: {e}", execution_time)


async def main():
    """Главная функция."""
    print("🚀 ФИНАЛЬНОЕ РЕШЕНИЕ COMET")
    print("="*60)
    print("✅ Открывает домен в Comet")
    print("✅ Отправляет промпт ассистенту")
    print("✅ Ждет результат")
    print("✅ Получает и передает результат")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Тест открытия домена")
    print("2. Тест промпта ассистенту")
    print("3. Полный цикл извлечения")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        comet = FinalCometSolution()
        
        if choice == "1":
            # Тест открытия домена
            test_domain = "metallsnab-nn.ru"
            print(f"\n🌐 Тест открытия домена: {test_domain}")
            
            success = comet.open_domain_in_comet(test_domain)
            
            if success:
                print("✅ Домен открыт успешно!")
                print("👀 Проверьте что открылась правильная страница в Comet")
            else:
                print("❌ Не удалось открыть домен")
                
        elif choice == "2":
            # Тест промпта
            test_prompt = "Найди ИНН и email для этого сайта"
            print(f"\n🤖 Тест промпта: {test_prompt}")
            
            success = comet.send_prompt_to_assistant(test_prompt)
            
            if success:
                print("✅ Промпт отправлен!")
                print("⏳ Ждите результат от ассистента...")
            else:
                print("❌ Не удалось отправить промпт")
                
        elif choice == "3":
            # Полный цикл
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 Полный цикл для домена: {test_domain}")
            print("🔄 Будет выполнено:")
            print("   1. Открытие домена в Comet")
            print("   2. Отправка промпта ассистенту")
            print("   3. Ожидание результата")
            print("   4. Получение результата")
            
            result = await comet.extract_domain_info(test_domain, wait_time=20)
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   Домен: {result['domain']}")
            print(f"   Успех: {result['success']}")
            
            if result.get("success"):
                print(f"   ИНН: {result.get('inn', 'Не найден')}")
                print(f"   Email: {result.get('email', 'Не найден')}")
                print(f"   Время: {result.get('execution_time', 0):.2f}с")
            else:
                print(f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}")
            
        else:
            print("❌ Неверный выбор")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Программа прервана")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
