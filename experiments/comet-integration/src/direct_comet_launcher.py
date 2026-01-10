"""
ПРЯМОЙ ЗАПУСК COMET С URL
Новый подход: запускаем Comet сразу с нужным URL
"""
import asyncio
import sys
import time
import subprocess
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


class DirectCometLauncher:
    """Прямой запуск Comet с URL."""
    
    def __init__(self):
        logger.info("🚀 DirectCometLauncher инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # РАБОЧИЕ КООРДИНАТЫ
        self.input_field_x = int(self.screen_width * 0.85)   # Поле ввода ассистента
        self.input_field_y = int(self.screen_height * 0.92)
        
        # Пути к Comet
        self.comet_paths = [
            Path(r'C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe'),
            Path(r'C:\Program Files\Comet\Comet.exe'),
            Path(r'C:\Program Files (x86)\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Comet\Application\Comet.exe'),
        ]
        
        logger.info(f"🎯 Поле ввода ассистента: ({self.input_field_x}, {self.input_field_y})")
        logger.info(f"🌐 Путей к Comet: {len(self.comet_paths)}")
    
    def find_comet_executable(self) -> Path:
        """Найти исполняемый файл Comet."""
        for path in self.comet_paths:
            if path.exists():
                logger.info(f"✅ Найден Comet: {path}")
                return path
        
        logger.error("❌ Comet не найден!")
        return None
    
    def close_existing_comet(self) -> bool:
        """Закрыть существующие окна Comet."""
        try:
            logger.info("🔍 Поиск и закрытие существующих окон Comet...")
            
            # Поиск процессов Comet
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Comet.exe'], 
                                      capture_output=True, text=True, timeout=5)
                if 'Comet.exe' in result.stdout:
                    logger.info("📍 Найдены процессы Comet, закрываю...")
                    subprocess.run(['taskkill', '/F', '/IM', 'Comet.exe'], 
                                  capture_output=True, timeout=5)
                    time.sleep(2)
            except:
                pass
            
            # Поиск окон
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    logger.info(f"📍 Найдено {len(windows)} окон Comet, закрываю...")
                    for window in windows:
                        try:
                            window.close()
                        except:
                            pass
                    time.sleep(2)
            
            logger.info("✅ Существующие окна Comet закрыты")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия Comet: {e}")
            return False
    
    def launch_comet_with_url(self, url: str) -> bool:
        """Запустить Comet с указанным URL."""
        try:
            logger.info(f"🚀 Запуск Comet с URL: {url}")
            
            # Найти исполняемый файл
            comet_exe = self.find_comet_executable()
            if not comet_exe:
                return False
            
            # Закрыть существующие окна
            self.close_existing_comet()
            
            # Запуск Comet с URL
            logger.info(f"📍 Запуск: {comet_exe} {url}")
            process = subprocess.Popen([str(comet_exe), url], 
                                      shell=True,
                                      creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Ждем загрузки
            logger.info("⏳ Ожидаю загрузки Comet...")
            time.sleep(8)  # Увеличиваем время для полной загрузки
            
            # Проверяем что Comet открыт
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    logger.info(f"✅ Comet открыт: {windows[0].title}")
                    return True
                else:
                    logger.error("❌ Comet не найден после запуска")
                    return False
            else:
                logger.info("✅ Comet запущен (нет проверки окон)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Comet: {e}")
            return False
    
    def verify_url_loaded(self, expected_url: str) -> bool:
        """Проверить что URL загружен."""
        try:
            logger.info(f"🔍 Проверка что загружен URL: {expected_url}")
            
            if not PYGETWINDOW_AVAILABLE:
                logger.warning("⚠️ Невозможно проверить URL без pygetwindow")
                return True  # Считаем успехом
            
            # Активировать окно Comet
            windows = gw.getWindowsWithTitle('Comet')
            if not windows:
                logger.error("❌ Окна Comet не найдены")
                return False
            
            window = windows[0]
            window.activate()
            time.sleep(1)
            
            # Пробуем получить URL через адресную строку
            logger.info("📍 Попытка получить URL из адресной строки...")
            
            # Ctrl+L - фокус на адресную строку
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1)
            
            # Ctrl+A - выделить все
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # Ctrl+C - копировать
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                actual_url = pyperclip.paste()
                logger.info(f"📋 Фактический URL: {actual_url}")
                
                if expected_url in actual_url:
                    logger.info("✅ URL загружен правильно!")
                    return True
                else:
                    logger.warning(f"⚠️ URL не совпадает. Ожидаемый: {expected_url}, Фактический: {actual_url}")
                    return False
            else:
                logger.warning("⚠️ Невозможно проверить URL без pyperclip")
                return True  # Считаем успехом
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки URL: {e}")
            return False
    
    def send_prompt_to_assistant(self, prompt: str) -> bool:
        """Отправить промпт ассистенту."""
        try:
            logger.info(f"🤖 Отправка промпта ассистенту: {prompt}")
            
            # Активировать окно Comet
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    windows[0].activate()
                    time.sleep(1)
            
            # Alt+A - открыть ассистента
            logger.info("📍 Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Клик по полю ввода
            logger.info(f"📍 Клик по полю ввода: ({self.input_field_x}, {self.input_field_y})")
            pyautogui.click(self.input_field_x, self.input_field_y)
            time.sleep(1)
            
            # Очистить поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Ввести промпт
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(1)
            
            # Enter
            logger.info("📍 Enter - отправка промпта...")
            pyautogui.press('enter')
            time.sleep(1)
            
            logger.info("✅ Промпт отправлен!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    def wait_and_get_response(self, max_wait_time: int = 30) -> Dict[str, Any]:
        """Подождать и получить ответ."""
        result = {
            "success": False,
            "inn": None,
            "email": None,
            "response_text": "",
            "error": None
        }
        
        try:
            logger.info(f"⏳ Ожидаю ответа {max_wait_time} секунд...")
            
            for i in range(max_wait_time):
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    logger.info(f"   ⏳ Прошло {i + 1}/{max_wait_time} секунд...")
            
            logger.info("✅ Ожидание завершено")
            
            # Получить ответ
            logger.info("📥 Получение ответа...")
            
            # Alt+A - убедиться что ассистент открыт
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Выделить все
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # Копировать
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                response = pyperclip.paste()
                result["response_text"] = response
                logger.info(f"📋 Получен ответ: {len(response)} символов")
                
                if len(response) < 50:
                    result["error"] = "Ответ ассистента слишком короткий"
                    return result
                
                # Поиск ИНН
                inn_patterns = [r'\b\d{10}\b', r'\b\d{12}\b', r'ИНН[:\s]+(\d{10,12})']
                for pattern in inn_patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches:
                        inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        inn = re.sub(r'[^\d]', '', str(inn))
                        if len(inn) in [10, 12]:
                            result["inn"] = inn
                            break
                
                # Поиск email
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_matches = re.findall(email_pattern, response)
                if email_matches:
                    result["email"] = email_matches[0]
                
                if result["inn"] or result["email"]:
                    result["success"] = True
                    logger.info(f"✅ Найдено: ИНН={result['inn']}, Email={result['email']}")
                else:
                    result["error"] = "ИНН и email не найдены в ответе"
                    logger.warning("⚠️ ИНН и email не найдены")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответа: {e}")
            result["error"] = str(e)
            return result
    
    async def extract_domain_info_direct(self, domain: str) -> Dict[str, Any]:
        """Извлечь информацию о домене прямым методом."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 ПРЯМОЕ извлечение для {domain}")
            logger.info("="*60)
            
            url = f"https://{domain}"
            
            # Шаг 1: Запуск Comet с URL
            logger.info("📍 ШАГ 1: Запуск Comet с URL")
            if not self.launch_comet_with_url(url):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось запустить Comet с URL",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 2: Проверка URL
            logger.info("📍 ШАГ 2: Проверка URL")
            if not self.verify_url_loaded(url):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "URL не загружен правильно",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 3: Отправка промпта
            logger.info("📍 ШАГ 3: Отправка промпта")
            prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
            if not self.send_prompt_to_assistant(prompt):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось отправить промпт",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 4: Получение ответа
            logger.info("📍 ШАГ 4: Получение ответа")
            response_result = self.wait_and_get_response(30)
            
            # Формирование результата
            result = {
                "domain": domain,
                "success": response_result["success"],
                "inn": response_result["inn"],
                "email": response_result["email"],
                "response_text": response_result["response_text"][:200] + "..." if len(response_result["response_text"]) > 200 else response_result["response_text"],
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if response_result["error"]:
                result["error"] = response_result["error"]
            
            if result["success"]:
                logger.info(f"✅ ПРЯМОЙ МЕТОД УСПЕШЕН!")
                logger.info(f"   ИНН: {result['inn']}")
                logger.info(f"   Email: {result['email']}")
            else:
                logger.warning(f"⚠️ ПРЯМОЙ МЕТОД НЕ УСПЕШЕН: {result.get('error', 'Неизвестная ошибка')}")
            
            logger.info("="*60)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка прямого метода: {e}")
            return {
                "domain": domain,
                "success": False,
                "error": f"Критическая ошибка: {e}",
                "execution_time": execution_time
            }


async def main():
    """Главная функция."""
    print("🚀 ПРЯМОЙ ЗАПУСК COMET С URL")
    print("="*60)
    print("✅ Новый подход: Comet запускается сразу с нужным URL")
    print("✅ Минимум манипуляций с адресной строкой")
    print("✅ Прямая работа с ассистентом")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Тест запуска Comet с URL")
    print("2. Тест промпта ассистенту")
    print("3. Полный цикл (ПРЯМОЙ МЕТОД)")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        launcher = DirectCometLauncher()
        
        if choice == "1":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🌐 Тест запуска Comet с URL: {test_domain}")
            
            success = launcher.launch_comet_with_url(f"https://{test_domain}")
            
            if success:
                print("✅ Comet запущен с URL!")
                print("👀 Проверьте что открылась правильная страница")
            else:
                print("❌ Не удалось запустить Comet с URL")
                
        elif choice == "2":
            test_prompt = "Найди ИНН и email для этого сайта"
            print(f"\n🤖 Тест промпта: {test_prompt}")
            
            success = launcher.send_prompt_to_assistant(test_prompt)
            
            if success:
                print("✅ Промпт отправлен!")
                print("⏳ Ждите результат от ассистента...")
            else:
                print("❌ Не удалось отправить промпт")
                
        elif choice == "3":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 Полный цикл (ПРЯМОЙ МЕТОД): {test_domain}")
            print("🔄 Новый подход:")
            print("   1. Запуск Comet с нужным URL")
            print("   2. Проверка загрузки страницы")
            print("   3. Отправка промпта ассистенту")
            print("   4. Получение ответа")
            
            result = await launcher.extract_domain_info_direct(test_domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ ПРЯМОГО МЕТОДА:")
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
                print(f"   📋 Ошибка: {result.get('error', 'Неизвестная ошибка')}")
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
