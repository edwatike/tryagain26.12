"""
РЕАЛЬНАЯ ПРОВЕРКА АССИСТЕНТА COMET
Проверяет что ассистент ДЕЙСТВИТЕЛЬНО запущен и промпт введен
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


class RealAssistantChecker:
    """Реальная проверка ассистента."""
    
    def __init__(self):
        logger.info("🚀 RealAssistantChecker инициализирован")
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
    
    def check_assistant_really_open(self) -> bool:
        """РЕАЛЬНО проверить что ассистент открыт."""
        try:
            logger.info("🔍 РЕАЛЬНАЯ проверка открытия ассистента...")
            
            # Активировать окно Comet
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if not windows:
                    logger.error("❌ Окна Comet не найдены")
                    return False
                
                windows[0].activate()
                time.sleep(1)
            
            # Пробуем Alt+A несколько раз
            logger.info("📍 Пробую Alt+A...")
            for i in range(3):
                pyautogui.hotkey('alt', 'a')
                time.sleep(2)
                
                # Проверяем что поле ввода активно
                logger.info(f"📍 Попытка {i+1}: проверка поля ввода...")
                
                # Клик по координатам поля ввода
                pyautogui.click(self.input_field_x, self.input_field_y)
                time.sleep(0.5)
                
                # Пробуем ввести тестовый символ
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.press('delete')
                time.sleep(0.5)
                pyautogui.typewrite('TEST')
                time.sleep(0.5)
                
                # Проверяем что введено
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                if PYPERCLIP_AVAILABLE:
                    clipboard_content = pyperclip.paste()
                    logger.info(f"📋 В буфере: '{clipboard_content}'")
                    
                    if 'TEST' in clipboard_content:
                        logger.info("✅ Ассистент ДЕЙСТВИТЕЛЬНО открыт и готов к вводу!")
                        # Очищаем тест
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.5)
                        pyautogui.press('delete')
                        time.sleep(0.5)
                        return True
                    else:
                        logger.warning(f"⚠️ Тест не пройден: '{clipboard_content}'")
                else:
                    logger.warning("⚠️ Невозможно проверить без pyperclip")
            
            logger.error("❌ Ассистент НЕ открылся после 3 попыток")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки ассистента: {e}")
            return False
    
    def send_prompt_and_really_check(self, prompt: str) -> bool:
        """Отправить промпт и РЕАЛЬНО проверить что он введен."""
        try:
            logger.info(f"🤖 Отправка промпта с РЕАЛЬНОЙ проверкой: {prompt}")
            
            # Проверить что ассистент открыт
            if not self.check_assistant_really_open():
                logger.error("❌ Ассистент не открыт, не могу отправить промпт")
                return False
            
            # Ввести промпт
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(1)
            
            # Проверить что промпт введен
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                actual_prompt = pyperclip.paste()
                logger.info(f"📋 Введено: '{actual_prompt[:100]}...'")
                
                if prompt[:50] in actual_prompt:  # Проверяем по первым 50 символам
                    logger.info("✅ Промпт ДЕЙСТВИТЕЛЬНО введен!")
                else:
                    logger.error(f"❌ Промпт введен НЕПРАВИЛЬНО: '{actual_prompt}'")
                    return False
            else:
                logger.warning("⚠️ Невозможно проверить ввод промпта")
            
            # Отправить промпт
            logger.info("📍 Enter - отправка промпта...")
            pyautogui.press('enter')
            time.sleep(1)
            
            logger.info("✅ Промпт отправлен!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    def wait_and_get_real_response(self, max_wait_time: int = 45) -> Dict[str, Any]:
        """Подождать и получить РЕАЛЬНЫЙ ответ."""
        result = {
            "success": False,
            "inn": None,
            "email": None,
            "response_text": "",
            "error": None
        }
        
        try:
            logger.info(f"⏳ Ожидаю РЕАЛЬНЫЙ ответ {max_wait_time} секунд...")
            
            for i in range(max_wait_time):
                time.sleep(1)
                if (i + 1) % 10 == 0:  # Каждые 10 секунд
                    logger.info(f"   ⏳ Прошло {i + 1}/{max_wait_time} секунд...")
            
            logger.info("✅ Ожидание завершено")
            
            # Получить ответ
            logger.info("📥 Получение РЕАЛЬНОГО ответа...")
            
            # Alt+A - убедиться что ассистент открыт
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Пробуем разные способы получить ответ
            logger.info("📍 Способ 1: Ctrl+A в ассистенте...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            if PYPERCLIP_AVAILABLE:
                response = pyperclip.paste()
                result["response_text"] = response
                logger.info(f"📋 Получен ответ: {len(response)} символов")
                
                if len(response) > 100:
                    logger.info("✅ Ответ достаточно длинный, анализирую...")
                    
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
                else:
                    result["error"] = f"Ответ слишком короткий: {len(response)} символов"
                    logger.warning(f"⚠️ Ответ слишком короткий: {len(response)} символов")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответа: {e}")
            result["error"] = str(e)
            return result
    
    async def real_extract_domain_info(self, domain: str) -> Dict[str, Any]:
        """РЕАЛЬНОЕ извлечение информации о домене."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 РЕАЛЬНОЕ извлечение для {domain}")
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
            
            # Шаг 2: РЕАЛЬНАЯ проверка ассистента
            logger.info("📍 ШАГ 2: РЕАЛЬНАЯ проверка ассистента")
            if not self.check_assistant_really_open():
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Ассистент не открыт или не готов",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 3: Отправка промпта с РЕАЛЬНОЙ проверкой
            logger.info("📍 ШАГ 3: Отправка промпта с РЕАЛЬНОЙ проверкой")
            prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
            if not self.send_prompt_and_really_check(prompt):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Промпт не введен правильно",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 4: Получение РЕАЛЬНОГО ответа
            logger.info("📍 ШАГ 4: Получение РЕАЛЬНОГО ответа")
            response_result = self.wait_and_get_real_response(45)
            
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
                logger.info(f"✅ РЕАЛЬНОЕ извлечение УСПЕШНО!")
                logger.info(f"   ИНН: {result['inn']}")
                logger.info(f"   Email: {result['email']}")
            else:
                logger.warning(f"⚠️ РЕАЛЬНОЕ извлечение НЕ УСПЕШНО: {result.get('error', 'Неизвестная ошибка')}")
            
            logger.info("="*60)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка РЕАЛЬНОГО извлечения: {e}")
            return {
                "domain": domain,
                "success": False,
                "error": f"Критическая ошибка: {e}",
                "execution_time": execution_time
            }


async def main():
    """Главная функция."""
    print("🚀 РЕАЛЬНАЯ ПРОВЕРКА АССИСТЕНТА COMET")
    print("="*60)
    print("✅ Проверяет что ассистент ДЕЙСТВИТЕЛЬНО запущен")
    print("✅ Проверяет что промпт ДЕЙСТВИТЕЛЬНО введен")
    print("✅ Увеличено время ожидания ответа")
    print("✅ РЕАЛЬНАЯ проверка каждого шага")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. РЕАЛЬНАЯ проверка ассистента")
    print("2. РЕАЛЬНЫЙ тест промпта")
    print("3. Полный цикл (РЕАЛЬНЫЙ)")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        checker = RealAssistantChecker()
        
        if choice == "1":
            print(f"\n🔍 РЕАЛЬНАЯ проверка ассистента...")
            
            success = checker.check_assistant_really_open()
            
            if success:
                print("✅ Ассистент ДЕЙСТВИТЕЛЬНО открыт и готов!")
            else:
                print("❌ Ассистент НЕ открыт или не готов")
                
        elif choice == "2":
            test_prompt = "Найди ИНН и email для этого сайта"
            print(f"\n🤖 РЕАЛЬНЫЙ тест промпта: {test_prompt}")
            
            success = checker.send_prompt_and_really_check(test_prompt)
            
            if success:
                print("✅ Промпт ДЕЙСТВИТЕЛЬНО введен и отправлен!")
            else:
                print("❌ Промпт НЕ введен правильно")
                
        elif choice == "3":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 Полный цикл (РЕАЛЬНЫЙ): {test_domain}")
            print("🔄 РЕАЛЬНАЯ проверка всех шагов:")
            print("   1. Запуск Comet с URL")
            print("   2. РЕАЛЬНАЯ проверка открытия ассистента")
            print("   3. РЕАЛЬНАЯ проверка ввода промпта")
            print("   4. Получение РЕАЛЬНОГО ответа")
            
            result = await checker.real_extract_domain_info(test_domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ РЕАЛЬНОЙ ПРОВЕРКИ:")
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
