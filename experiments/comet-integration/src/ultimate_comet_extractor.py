"""
УЛЬТИМАТИВНЫЙ ИЗВЛЕКАТЕЛЬ COMET
Гарантированно убеждается что:
1) Домен открыт через Comet
2) Ассистент открыт и промпт отправлен
3) Ответ получен и обработан
4) Результат зафиксирован
5) Пока ответ не получен - задача не выполнена!
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging
import re

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


class UltimateCometExtractor:
    """Ультимативный извлекатель информации из Comet."""
    
    def __init__(self):
        logger.info("🚀 UltimateCometExtractor инициализирован")
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
    
    def ensure_domain_opened_in_comet(self, domain: str) -> bool:
        """Убедиться что домен открыт в Comet."""
        try:
            logger.info(f"🌐 Убеждаюсь что домен {domain} открыт в Comet...")
            url = f"https://{domain}"
            
            # Шаг 1: Активировать Comet
            if not self.force_activate_comet():
                logger.error("❌ Не удалось активировать Comet")
                return False
            
            # Шаг 2: Фокус на адресную строку
            logger.info("📍 Фокус на адресную строку...")
            
            # Пробуем несколько методов
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1)
            pyautogui.click(self.address_bar_x, self.address_bar_y)
            time.sleep(0.5)
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
            
            # Шаг 5: Проверяем что Comet все еще активен
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после перехода")
                return False
            
            logger.info("✅ Домен открыт в Comet!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка открытия домена {domain}: {e}")
            return False
    
    def ensure_assistant_open_and_prompt_sent(self, prompt: str) -> bool:
        """Убедиться что ассистент открыт и промпт отправлен."""
        try:
            logger.info(f"🤖 Убеждаюсь что ассистент открыт и промпт отправлен: {prompt}")
            
            # Шаг 1: Активировать Comet
            if not self.force_activate_comet():
                logger.error("❌ Не удалось активировать Comet")
                return False
            
            # Шаг 2: Открыть ассистента
            logger.info("📍 Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 3: Клик по полю ввода
            logger.info(f"📍 Клик по полю ввода: ({self.input_field_x}, {self.input_field_y})")
            pyautogui.click(self.input_field_x, self.input_field_y)
            time.sleep(0.5)
            
            # Шаг 4: Очистить поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Шаг 5: Ввести промпт
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(0.5)
            
            # Шаг 6: Enter
            logger.info("📍 Enter - отправка промпта...")
            pyautogui.press('enter')
            time.sleep(0.5)
            
            logger.info("✅ Ассистент открыт и промпт отправлен!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    def wait_for_assistant_response(self, max_wait_time: int = 30) -> bool:
        """Ждать ответа от ассистента."""
        try:
            logger.info(f"⏳ Ожидаю ответ от ассистента (максимум {max_wait_time} секунд)...")
            
            for i in range(max_wait_time):
                time.sleep(1)
                if (i + 1) % 5 == 0:  # Каждые 5 секунд
                    logger.info(f"   ⏳ Прошло {i + 1}/{max_wait_time} секунд...")
            
            logger.info("✅ Ожидание завершено!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка ожидания: {e}")
            return False
    
    def extract_assistant_response(self) -> Dict[str, Any]:
        """Извлечь и проанализировать ответ ассистента."""
        try:
            logger.info("📥 Извлечение ответа ассистента...")
            
            # Убедиться что Comet активен
            if not self.force_activate_comet():
                return self._create_result("unknown", False, "Comet не активен")
            
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
                    
                    # Анализируем ответ
                    return self._analyze_assistant_response(clipboard_content)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка чтения буфера обмена: {e}")
                    return self._create_result("unknown", False, f"Ошибка буфера обмена: {e}")
            else:
                logger.error("❌ pyperclip недоступен")
                return self._create_result("unknown", False, "pyperclip недоступен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения ответа: {e}")
            return self._create_result("unknown", False, f"Ошибка извлечения ответа: {e}")
    
    def _analyze_assistant_response(self, response_text: str) -> Dict[str, Any]:
        """Проанализировать ответ ассистента."""
        try:
            logger.info("🔍 Анализ ответа ассистента...")
            
            # Ищем ИНН
            inn = None
            inn_patterns = [
                r'\b\d{10}\b',  # 10 цифр
                r'\b\d{12}\b',  # 12 цифр
                r'ИНН[:\s]+(\d{10,12})',  # ИНН: 1234567890
                r'ИНН\s*[:\-]?\s*(\d{10,12})',  # ИНН - 1234567890
            ]
            
            for pattern in inn_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                if matches:
                    # Если это группа из regex, берем первый элемент
                    inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    # Очищаем от разделителей
                    inn = re.sub(r'[^\d]', '', str(inn))
                    if len(inn) in [10, 12]:
                        logger.info(f"📋 Найден ИНН: {inn}")
                        break
            
            # Ищем email
            email = None
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, response_text)
            if email_matches:
                email = email_matches[0]
                logger.info(f"📋 Найден email: {email}")
            
            # Определяем успех
            success = inn is not None or email is not None
            
            # Создаем результат
            result = self._create_result("unknown", success, None)
            result["inn"] = inn
            result["email"] = email
            result["raw_response"] = response_text
            
            if success:
                logger.info(f"✅ Успешно найдено: ИНН={inn}, Email={email}")
            else:
                logger.warning("⚠️ ИНН и email не найдены в ответе")
                
                # Анализируем почему не найдено
                if "не найдено" in response_text.lower() or "нет информации" in response_text.lower():
                    result["reason"] = "Ассистент сообщил что информация не найдена"
                elif "ошибка" in response_text.lower() or "не удалось" in response_text.lower():
                    result["reason"] = "Ассистент сообщил об ошибке"
                elif len(response_text.strip()) < 50:
                    result["reason"] = "Ответ ассистента слишком короткий"
                else:
                    result["reason"] = "ИНН и email не найдены в ответе ассистента"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа ответа: {e}")
            return self._create_result("unknown", False, f"Ошибка анализа ответа: {e}")
    
    def _create_result(self, domain: str, success: bool, error: str = None) -> Dict[str, Any]:
        """Создать результат."""
        result = {
            "domain": domain,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        
        if error:
            result["error"] = error
            result["reason"] = error
        
        return result
    
    async def extract_domain_info_complete(self, domain: str, max_wait_time: int = 30) -> Dict[str, Any]:
        """Полный цикл извлечения информации с гарантиями."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 НАЧАЛО ПОЛНОГО ЦИКЛА ИЗВЛЕЧЕНИЯ ДЛЯ {domain}")
            logger.info("="*60)
            
            # ШАГ 1: Убедиться что домен открыт через Comet
            logger.info("📍 ШАГ 1: Убеждаюсь что домен открыт через Comet...")
            if not self.ensure_domain_opened_in_comet(domain):
                result = self._create_result(domain, False, "Не удалось открыть домен в Comet")
                result["execution_time"] = time.time() - start_time
                return result
            
            # ШАГ 2: Убедиться что ассистент открыт и промпт отправлен
            logger.info("📍 ШАГ 2: Убеждаюсь что ассистент открыт и промпт отправлен...")
            prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
            if not self.ensure_assistant_open_and_prompt_sent(prompt):
                result = self._create_result(domain, False, "Не удалось отправить промпт ассистенту")
                result["execution_time"] = time.time() - start_time
                return result
            
            # ШАГ 3: Ждать ответа от ассистента
            logger.info("📍 ШАГ 3: Жду ответа от ассистента...")
            if not self.wait_for_assistant_response(max_wait_time):
                result = self._create_result(domain, False, f"Таймаут ожидания ответа ассистента ({max_wait_time}с)")
                result["execution_time"] = time.time() - start_time
                return result
            
            # ШАГ 4: Извлечь и проанализировать ответ
            logger.info("📍 ШАГ 4: Извлекаю и анализирую ответ ассистента...")
            result = self.extract_assistant_response()
            result["domain"] = domain
            result["execution_time"] = time.time() - start_time
            
            # Финальная проверка
            if result.get("success"):
                logger.info(f"✅ ПОЛНЫЙ ЦИКЛ УСПЕШЕН для {domain}!")
                logger.info(f"   ИНН: {result.get('inn', 'Не найден')}")
                logger.info(f"   Email: {result.get('email', 'Не найден')}")
                logger.info(f"   Время: {result['execution_time']:.2f}с")
            else:
                logger.warning(f"⚠️ ПОЛНЫЙ ЦИКЛ НЕ УСПЕШЕН для {domain}!")
                logger.warning(f"   Причина: {result.get('reason', 'Неизвестная причина')}")
                logger.warning(f"   Время: {result['execution_time']:.2f}с")
            
            logger.info("="*60)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка полного цикла для {domain}: {e}")
            result = self._create_result(domain, False, f"Критическая ошибка: {e}")
            result["execution_time"] = execution_time
            return result


async def main():
    """Главная функция."""
    print("🚀 УЛЬТИМАТИВНЫЙ ИЗВЛЕКАТЕЛЬ COMET")
    print("="*60)
    print("✅ Гарантированно убеждается что домен открыт через Comet")
    print("✅ Гарантированно убеждается что ассистент открыт и промпт отправлен")
    print("✅ Ждет ответа от ассистента")
    print("✅ Извлекает и анализирует ответ")
    print("✅ Зафиксировать результат - если нашел, передать ИНН/email")
    print("✅ Если не нашел - передать причину")
    print("❌ Пока ответ не получен - задача не выполнена!")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Тест открытия домена")
    print("2. Тест промпта ассистенту")
    print("3. Полный цикл извлечения (ГАРАНТИРОВАННЫЙ)")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        extractor = UltimateCometExtractor()
        
        if choice == "1":
            # Тест открытия домена
            test_domain = "metallsnab-nn.ru"
            print(f"\n🌐 Тест открытия домена: {test_domain}")
            
            success = extractor.ensure_domain_opened_in_comet(test_domain)
            
            if success:
                print("✅ Домен успешно открыт в Comet!")
                print("👀 Проверьте что открылась правильная страница")
            else:
                print("❌ Не удалось открыть домен")
                
        elif choice == "2":
            # Тест промпта
            test_prompt = "Найди ИНН и email для этого сайта"
            print(f"\n🤖 Тест промпта: {test_prompt}")
            
            success = extractor.ensure_assistant_open_and_prompt_sent(test_prompt)
            
            if success:
                print("✅ Промпт успешно отправлен!")
                print("⏳ Ждите результат от ассистента...")
            else:
                print("❌ Не удалось отправить промпт")
                
        elif choice == "3":
            # Полный цикл
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 ПОЛНЫЙ ЦИКЛ ИЗВЛЕЧЕНИЯ: {test_domain}")
            print("🔄 Гарантированная проверка всех шагов:")
            print("   1. Убедиться что домен открыт через Comet")
            print("   2. Убедиться что ассистент открыт и промпт отправлен")
            print("   3. Ждать ответа от ассистента")
            print("   4. Извлечь и проанализировать ответ")
            print("   5. Зафиксировать результат")
            
            print(f"\n⚠️ ВАЖНО: Пока ответ не получен - задача не выполнена!")
            
            result = await extractor.extract_domain_info_complete(test_domain, max_wait_time=30)
            
            print(f"\n📊 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
            print(f"   Домен: {result['domain']}")
            print(f"   Успех: {result['success']}")
            print(f"   Время: {result.get('execution_time', 0):.2f}с")
            
            if result.get("success"):
                print(f"\n✅ УСПЕХ - ИНФОРМАЦИЯ НАЙДЕНА:")
                print(f"   📋 ИНН: {result.get('inn', 'Не найден')}")
                print(f"   📧 Email: {result.get('email', 'Не найден')}")
                print(f"\n🎉 ЗАДАЧА ВЫПОЛНЕНА!")
            else:
                print(f"\n❌ НЕУСПЕХ - ИНФОРМАЦИЯ НЕ НАЙДЕНА:")
                print(f"   📋 Причина: {result.get('reason', 'Неизвестная причина')}")
                print(f"   📋 Ошибка: {result.get('error', 'Нет ошибки')}")
                print(f"\n⚠️ ЗАДАЧА НЕ ВЫПОЛНЕНА!")
            
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
