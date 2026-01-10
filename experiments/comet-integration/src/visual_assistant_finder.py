"""
ВИЗУАЛЬНЫЙ ПОИСК АССИСТЕНТА COMET
Ищет ассистента на странице и открывает его
"""
import asyncio
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
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


class VisualAssistantFinder:
    """Визуальный поиск ассистента."""
    
    def __init__(self):
        logger.info("🚀 VisualAssistantFinder инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # Пути к Comet
        self.comet_paths = [
            Path(r'C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe'),
            Path(r'C:\Program Files\Comet\Comet.exe'),
            Path(r'C:\Program Files (x86)\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Comet\Application\Comet.exe'),
        ]
        
        # Возможные места где может быть ассистент
        self.assistant_locations = [
            # Правый нижний угол
            (int(self.screen_width * 0.9), int(self.screen_height * 0.9)),
            (int(self.screen_width * 0.85), int(self.screen_height * 0.85)),
            (int(self.screen_width * 0.95), int(self.screen_height * 0.95)),
            
            # Правый верхний угол
            (int(self.screen_width * 0.9), int(self.screen_height * 0.1)),
            (int(self.screen_width * 0.85), int(self.screen_height * 0.15)),
            
            # Центр справа
            (int(self.screen_width * 0.9), int(self.screen_height * 0.5)),
            (int(self.screen_width * 0.85), int(self.screen_height * 0.5)),
            
            # Нижняя панель
            (int(self.screen_width * 0.5), int(self.screen_height * 0.95)),
            (int(self.screen_width * 0.3), int(self.screen_height * 0.95)),
            (int(self.screen_width * 0.7), int(self.screen_height * 0.95)),
        ]
        
        logger.info(f"🔍 Точек для поиска ассистента: {len(self.assistant_locations)}")
    
    def find_comet_executable(self) -> Path:
        """Найти исполняемый файл Comet."""
        for path in self.comet_paths:
            if path.exists():
                logger.info(f"✅ Найден Comet: {path}")
                return path
        logger.error("❌ Comet не найден!")
        return None
    
    def launch_comet_with_url(self, url: str) -> bool:
        """Запустить Comet с указанным URL."""
        try:
            logger.info(f"🚀 Запуск Comet с URL: {url}")
            
            comet_exe = self.find_comet_executable()
            if not comet_exe:
                return False
            
            # Закрыть существующие окна
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Comet.exe'], 
                                      capture_output=True, text=True, timeout=5)
                if 'Comet.exe' in result.stdout:
                    subprocess.run(['taskkill', '/F', '/IM', 'Comet.exe'], 
                                  capture_output=True, timeout=5)
                    time.sleep(2)
            except:
                pass
            
            # Запуск Comet с URL
            logger.info(f"📍 Запуск: {comet_exe} {url}")
            subprocess.Popen([str(comet_exe), url], shell=True)
            
            # Ждем загрузки
            logger.info("⏳ Ожидаю загрузки Comet...")
            time.sleep(8)
            
            # Проверяем что Comet открыт
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    logger.info(f"✅ Comet открыт: {windows[0].title}")
                    return True
            
            logger.error("❌ Comet не найден после запуска")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Comet: {e}")
            return False
    
    def activate_comet_window(self) -> bool:
        """Активировать окно Comet."""
        try:
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    windows[0].activate()
                    time.sleep(1)
                    return True
            return False
        except:
            return False
    
    def try_all_assistant_open_methods(self) -> bool:
        """Попробовать все способы открытия ассистента."""
        logger.info("🔍 Пробую все способы открытия ассистента...")
        
        methods = [
            ("Alt+A", lambda: pyautogui.hotkey('alt', 'a')),
            ("Ctrl+Shift+A", lambda: pyautogui.hotkey('ctrl', 'shift', 'a')),
            ("F1", lambda: pyautogui.press('f1')),
            ("Ctrl+/", lambda: pyautogui.hotkey('ctrl', '/')),
            ("Ctrl+K", lambda: pyautogui.hotkey('ctrl', 'k')),
        ]
        
        for method_name, method_func in methods:
            logger.info(f"🔄 Пробую {method_name}...")
            try:
                method_func()
                time.sleep(3)
                
                # Проверяем что ассистент открыт
                if self.check_assistant_open():
                    logger.info(f"✅ {method_name} сработал!")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Ошибка с {method_name}: {e}")
        
        return False
    
    def check_assistant_open(self) -> bool:
        """Проверить что ассистент открыт."""
        try:
            # Пробуем ввести тестовый символ
            test_x, test_y = int(self.screen_width * 0.85), int(self.screen_height * 0.92)
            pyautogui.click(test_x, test_y)
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            pyautogui.typewrite('TEST')
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                clipboard_content = pyperclip.paste()
                if 'TEST' in clipboard_content:
                    # Очищаем тест
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
                    return True
            
            return False
        except:
            return False
    
    def visual_search_assistant(self) -> bool:
        """Визуально поискать ассистента."""
        logger.info("🔍 Визуальный поиск ассистента...")
        
        for i, (x, y) in enumerate(self.assistant_locations):
            logger.info(f"🔄 Проверяю точку {i+1}/{len(self.assistant_locations)}: ({x}, {y})")
            
            # Клик по точке
            pyautogui.click(x, y)
            time.sleep(1)
            
            # Пробуем разные комбинации после клика
            pyautogui.hotkey('ctrl', 'shift', 'a')
            time.sleep(2)
            
            if self.check_assistant_open():
                logger.info(f"✅ Ассистент найден в точке {i+1}!")
                return True
            
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if self.check_assistant_open():
                logger.info(f"✅ Ассистент найден в точке {i+1}!")
                return True
        
        return False
    
    def interactive_assistant_search(self) -> bool:
        """Интерактивный поиск ассистента."""
        logger.info("🔍 Интерактивный поиск ассистента...")
        
        print("\n🔍 ИНТЕРАКТИВНЫЙ ПОИСК АССИСТЕНТА")
        print("="*50)
        print("📍 Программа будет кликать в разные места экрана")
        print("📍 Если ассистент откроется - нажмите ENTER")
        print("📍 Для пропуска точки - нажмите любую другую клавишу")
        print("="*50)
        
        for i, (x, y) in enumerate(self.assistant_locations):
            print(f"\n🔄 Точка {i+1}/{len(self.assistant_locations)}: ({x}, {y})")
            print("📍 Нажмите ENTER для клика или любую другую клавишу для пропуска...")
            
            try:
                import keyboard
                if keyboard.read_key() != 'enter':
                    continue
            except:
                input("Нажмите ENTER для продолжения...")
            
            # Активируем окно Comet
            self.activate_comet_window()
            time.sleep(1)
            
            # Клик по точке
            pyautogui.click(x, y)
            time.sleep(2)
            
            # Пробуем открыть ассистента
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if self.check_assistant_open():
                logger.info(f"✅ Ассистент найден в точке {i+1}!")
                print(f"\n✅ АССИСТЕНТ НАЙДЕН В ТОЧКЕ {i+1}!")
                return True
        
        return False
    
    def send_prompt_and_get_response(self, prompt: str) -> Dict[str, Any]:
        """Отправить промпт и получить ответ."""
        result = {
            "success": False,
            "inn": None,
            "email": None,
            "response_text": "",
            "error": None
        }
        
        try:
            logger.info(f"🤖 Отправка промпта: {prompt}")
            
            # Ввести промпт
            input_x, input_y = int(self.screen_width * 0.85), int(self.screen_height * 0.92)
            pyautogui.click(input_x, input_y)
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(1)
            
            pyautogui.press('enter')
            time.sleep(1)
            
            logger.info("✅ Промпт отправлен!")
            
            # Ожидание ответа
            logger.info("⏳ Ожидаю ответ 45 секунд...")
            for i in range(45):
                time.sleep(1)
                if (i + 1) % 10 == 0:
                    logger.info(f"   ⏳ Прошло {i + 1}/45 секунд...")
            
            # Получение ответа
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            if PYPERCLIP_AVAILABLE:
                response = pyperclip.paste()
                result["response_text"] = response
                logger.info(f"📋 Получен ответ: {len(response)} символов")
                
                if len(response) > 100:
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
                        result["error"] = "ИНН и email не найдены"
                else:
                    result["error"] = f"Ответ слишком короткий: {len(response)} символов"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            result["error"] = str(e)
            return result
    
    async def visual_extract_domain_info(self, domain: str) -> Dict[str, Any]:
        """Визуальное извлечение информации."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 ВИЗУАЛЬНОЕ извлечение для {domain}")
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
            
            # Шаг 2: Поиск ассистента
            logger.info("📍 ШАГ 2: Поиск ассистента")
            
            # Пробуем все методы
            if self.try_all_assistant_open_methods():
                logger.info("✅ Ассистент открыт через клавиши")
            elif self.visual_search_assistant():
                logger.info("✅ Ассистент найден визуально")
            else:
                logger.error("❌ Ассистент не найден")
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Ассистент не найден",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 3: Отправка промпта
            logger.info("📍 ШАГ 3: Отправка промпта")
            prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
            response_result = self.send_prompt_and_get_response(prompt)
            
            # Формирование результата
            result = {
                "domain": domain,
                "success": response_result["success"],
                "inn": response_result["inn"],
                "email": response_result["email"],
                "response_preview": response_result["response_text"][:200] + "..." if len(response_result["response_text"]) > 200 else response_result["response_text"],
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if response_result["error"]:
                result["error"] = response_result["error"]
            
            if result["success"]:
                logger.info(f"✅ ВИЗУАЛЬНОЕ извлечение УСПЕШНО!")
            else:
                logger.warning(f"⚠️ ВИЗУАЛЬНОЕ извлечение НЕ УСПЕШНО")
            
            logger.info("="*60)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка ВИЗУАЛЬНОГО извлечения: {e}")
            return {
                "domain": domain,
                "success": False,
                "error": f"Критическая ошибка: {e}",
                "execution_time": execution_time
            }


async def main():
    """Главная функция."""
    print("🚀 ВИЗУАЛЬНЫЙ ПОИСК АССИСТЕНТА COMET")
    print("="*60)
    print("✅ Ищет ассистента на странице")
    print("✅ Пробует разные способы открытия")
    print("✅ Визуальный поиск в разных точках")
    print("✅ Интерактивный поиск")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Интерактивный поиск ассистента")
    print("2. Автоматический поиск ассистента")
    print("3. Полный цикл (ВИЗУАЛЬНЫЙ)")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        finder = VisualAssistantFinder()
        
        if choice == "1":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🔍 Интерактивный поиск ассистента для {test_domain}")
            
            # Запуск Comet
            if not finder.launch_comet_with_url(f"https://{test_domain}"):
                print("❌ Не удалось запустить Comet")
                return
            
            # Интерактивный поиск
            success = finder.interactive_assistant_search()
            
            if success:
                print("✅ Ассистент найден!")
            else:
                print("❌ Ассистент не найден")
                
        elif choice == "2":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🔍 Автоматический поиск ассистента для {test_domain}")
            
            # Запуск Comet
            if not finder.launch_comet_with_url(f"https://{test_domain}"):
                print("❌ Не удалось запустить Comet")
                return
            
            # Автоматический поиск
            if finder.try_all_assistant_open_methods():
                print("✅ Ассистент открыт через клавиши!")
            elif finder.visual_search_assistant():
                print("✅ Ассистент найден визуально!")
            else:
                print("❌ Ассистент не найден")
                
        elif choice == "3":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 Полный цикл (ВИЗУАЛЬНЫЙ): {test_domain}")
            print("🔄 Визуальный поиск ассистента:")
            print("   1. Запуск Comet с URL")
            print("   2. Поиск ассистента разными методами")
            print("   3. Отправка промпта")
            print("   4. Получение ответа")
            
            result = await finder.visual_extract_domain_info(test_domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ ВИЗУАЛЬНОГО ПОИСКА:")
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
