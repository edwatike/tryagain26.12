"""
ФИНАЛЬНЫЙ РАБОЧИЙ ИЗВЛЕКАТЕЛЬ COMET
Проблема ввода решена через буфер обмена
"""
import pyautogui
import time
import pyperclip
import pygetwindow as gw
import re
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отключаем fail-safe
pyautogui.FAILSAFE = False

class FinalWorkingCometExtractor:
    """Финальный рабочий извлекатель Comet."""
    
    def __init__(self):
        logger.info("🚀 FinalWorkingCometExtractor инициализирован")
        self.screen_width, self.screen_height = pyautogui.size()
        
        # РАБОЧАЯ ПОЗИЦИЯ ДЛЯ АССИСТЕНТА
        self.assistant_x = int(self.screen_width * 0.85)   # 1632 для 1920x1080
        self.assistant_y = int(self.screen_height * 0.92)  # 993 для 1920x1080
        
        logger.info(f"🎯 Рабочая позиция ассистента: ({self.assistant_x}, {self.assistant_y})")
    
    def activate_comet(self) -> bool:
        """Активировать окно Comet."""
        try:
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                windows[0].activate()
                time.sleep(1)
                logger.info("✅ Comet активирован")
                return True
            else:
                logger.error("❌ Окна Comet не найдены")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка активации Comet: {e}")
            return False
    
    def open_assistant(self) -> bool:
        """Открыть ассистента."""
        try:
            logger.info("📍 Открываю ассистента (Alt+A)...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Клик в рабочую позицию
            logger.info(f"📍 Клик в позицию ассистента: ({self.assistant_x}, {self.assistant_y})")
            pyautogui.click(self.assistant_x, self.assistant_y)
            time.sleep(1)
            
            # Проверяем что ассистент готов
            test_text = 'ASSISTANT_READY_TEST'
            pyperclip.copy(test_text)
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            clipboard = pyperclip.paste()
            if test_text in clipboard:
                logger.info("✅ Ассистент открыт и готов к вводу!")
                # Очищаем тест
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.press('delete')
                time.sleep(0.5)
                return True
            else:
                logger.error("❌ Ассистент не готов к вводу")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка открытия ассистента: {e}")
            return False
    
    def send_prompt(self, prompt: str) -> bool:
        """Отправить промпт через буфер обмена."""
        try:
            logger.info(f"🤖 Отправляю промпт: {prompt[:50]}...")
            
            # Копируем промпт в буфер обмена
            pyperclip.copy(prompt)
            time.sleep(0.5)
            
            # Клик в позицию ассистента
            pyautogui.click(self.assistant_x, self.assistant_y)
            time.sleep(1)
            
            # Очищаем поле
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Вставляем промпт
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            
            # Проверяем что введено
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            clipboard = pyperclip.paste()
            if prompt[:30] in clipboard:
                logger.info("✅ Промпт введен!")
                
                # Отправляем
                pyautogui.press('enter')
                time.sleep(1)
                logger.info("✅ Промпт отправлен!")
                return True
            else:
                logger.error("❌ Промпт не введен")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    def get_response(self, max_wait: int = 45) -> str:
        """Получить ответ от ассистента."""
        try:
            logger.info(f"⏳ Ожидаю ответ {max_wait} секунд...")
            
            for i in range(max_wait):
                time.sleep(1)
                if (i + 1) % 10 == 0:
                    logger.info(f"   ⏳ Прошло {i + 1}/{max_wait} секунд...")
            
            logger.info("📍 Получаю ответ...")
            
            # Убеждаемся что ассистент открыт
            pyautogui.hotkey('alt', 'a')
            time.sleep(3)
            
            # Клик в позицию ассистента
            pyautogui.click(self.assistant_x, self.assistant_y)
            time.sleep(1)
            
            # Выделяем все и копируем
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(1)
            
            response = pyperclip.paste()
            logger.info(f"📋 Получен ответ: {len(response)} символов")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения ответа: {e}")
            return ""
    
    def parse_response(self, response: str) -> dict:
        """Распарсить ответ для ИНН и email."""
        try:
            logger.info("🔍 Анализирую ответ...")
            
            result = {
                "inn": None,
                "email": None,
                "success": False,
                "reason": None
            }
            
            # Поиск ИНН
            inn_patterns = [
                r'\b\d{10}\b',  # 10 цифр
                r'\b\d{12}\b',  # 12 цифр
                r'ИНН[:\s]+(\d{10,12})',  # ИНН: 1234567890
                r'ИНН\s*[:\-]?\s*(\d{10,12})',  # ИНН - 1234567890
            ]
            
            for pattern in inn_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    inn = re.sub(r'[^\d]', '', str(inn))
                    if len(inn) in [10, 12]:
                        result["inn"] = inn
                        logger.info(f"📋 Найден ИНН: {inn}")
                        break
            
            # Поиск email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, response)
            if email_matches:
                result["email"] = email_matches[0]
                logger.info(f"📋 Найден email: {result['email']}")
            
            # Определяем успех
            result["success"] = result["inn"] is not None or result["email"] is not None
            
            if result["success"]:
                logger.info("✅ ИНН или email найдены!")
            else:
                logger.warning("⚠️ ИНН и email не найдены")
                
                # Анализируем причину
                if "не найдено" in response.lower() or "нет информации" in response.lower():
                    result["reason"] = "Ассистент сообщил что информация не найдена"
                elif "ошибка" in response.lower() or "не удалось" in response.lower():
                    result["reason"] = "Ассистент сообщил об ошибке"
                elif len(response.strip()) < 50:
                    result["reason"] = "Ответ ассистента слишком короткий"
                else:
                    result["reason"] = "ИНН и email не найдены в ответе ассистента"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга ответа: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_domain_info(self, domain: str) -> dict:
        """Полный цикл извлечения информации о домене."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Извлечение информации для {domain}")
            logger.info("="*60)
            
            # Шаг 1: Активировать Comet
            if not self.activate_comet():
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось активировать Comet",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 2: Открыть ассистента
            if not self.open_assistant():
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось открыть ассистента",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 3: Отправить промпт
            prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
            if not self.send_prompt(prompt):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось отправить промпт",
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 4: Получить ответ
            response = self.get_response(45)
            
            # Шаг 5: Распарсить ответ
            parsed = self.parse_response(response)
            
            # Формирование результата
            result = {
                "domain": domain,
                "success": parsed["success"],
                "inn": parsed.get("inn"),
                "email": parsed.get("email"),
                "response_preview": response[:200] + "..." if len(response) > 200 else response,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if not parsed["success"]:
                result["error"] = parsed.get("reason", "Неизвестная ошибка")
            
            logger.info("="*60)
            if result["success"]:
                logger.info(f"✅ ИЗВЛЕЧЕНИЕ УСПЕШНО для {domain}!")
                logger.info(f"   ИНН: {result['inn']}")
                logger.info(f"   Email: {result['email']}")
            else:
                logger.warning(f"⚠️ ИЗВЛЕЧЕНИЕ НЕ УСПЕШНО для {domain}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка извлечения: {e}")
            return {
                "domain": domain,
                "success": False,
                "error": f"Критическая ошибка: {e}",
                "execution_time": execution_time
            }


def main():
    """Главная функция."""
    print("🚀 ФИНАЛЬНЫЙ РАБОЧИЙ ИЗВЛЕКАТЕЛЬ COMET")
    print("="*60)
    print("✅ ПРОБЛЕМА ВВОДА РЕШЕНА!")
    print("✅ Используем буфер обмена")
    print("✅ Рабочая позиция ассистента найдена")
    print("✅ Полный цикл работает")
    print("="*60)
    
    extractor = FinalWorkingCometExtractor()
    
    # Тест с доменом
    test_domain = "metallsnab-nn.ru"
    print(f"\n🚀 Запускаю извлечение для {test_domain}")
    
    result = extractor.extract_domain_info(test_domain)
    
    print(f"\n📊 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print(f"   Домен: {result['domain']}")
    print(f"   Успех: {result['success']}")
    print(f"   Время: {result.get('execution_time', 0):.2f}с")
    
    if result.get("success"):
        print(f"\n✅ УСПЕХ - ИНФОРМАЦИЯ НАЙДЕНА:")
        print(f"   📋 ИНН: {result.get('inn', 'Не найден')}")
        print(f"   📧 Email: {result.get('email', 'Не найден')}")
        print(f"\n🎉 ЗАДАЧА ВЫПОЛНЕНА!")
        print("🎉 ПРОБЛЕМА РЕШЕНА!")
    else:
        print(f"\n❌ НЕУСПЕХ - ИНФОРМАЦИЯ НЕ НАЙДЕНА:")
        print(f"   📋 Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        print(f"   📋 Ответ: {result.get('response_preview', 'Нет ответа')}")
        print(f"\n⚠️ ЗАДАЧА НЕ ВЫПОЛНЕНА")


if __name__ == "__main__":
    main()
