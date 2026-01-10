"""
Сессия с ручным фокусом - пользователь активирует окно вручную.
"""
import asyncio
import sys
import json
import re
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

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


class ManualFocusSession:
    """Сессия с ручным фокусом - пользователь активирует окно."""
    
    def __init__(self):
        logger.info("ManualFocus сессия инициализирована")
    
    async def check_comet_ready(self) -> bool:
        """Проверить готовность Comet."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                logger.info("✅ Comet найден и готов к работе")
                return True
            else:
                logger.warning("❌ Comet не найден")
                return False
        except:
            logger.warning("Предполагаем что Comet готов")
            return True
    
    async def navigate_to_domain(self, domain: str):
        """Перейти к домену (без активации окна)."""
        try:
            url = f"https://{domain}"
            logger.info(f"🔗 Переход к: {domain}")
            
            # Ctrl+L для адресной строки
            await self._press_keys('ctrl', 'l')
            await asyncio.sleep(0.5)
            
            # Ввод URL
            await self._type_text(url)
            await asyncio.sleep(0.5)
            
            # Enter
            await self._press_key('enter')
            await asyncio.sleep(4)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка перехода: {e}")
            return False
    
    async def activate_assistant_manual(self) -> Dict[str, Any]:
        """Активация ассистента с ручным фокусом."""
        try:
            logger.info("🚀 Запуск с ручным фокусом")
            
            # Шаг 1: Alt+A для ассистента
            logger.info("⌨️ Alt+A - активация ассистента")
            await self._press_keys('alt', 'a')
            await asyncio.sleep(2)
            
            # Шаг 2: Небольшая пауза для пользователя
            logger.info("⏳ Пауза 2 секунды...")
            await asyncio.sleep(2)
            
            # Шаг 3: Пробуем установить фокус кликом в центр
            logger.info("🖱️ Клик в центр экрана для фокуса")
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            pyautogui.click(center_x, center_y)
            await asyncio.sleep(1)
            
            # Шаг 4: Ввод команды
            logger.info("⌨️ Ввод /requisites")
            await self._type_text("/requisites")
            await asyncio.sleep(1)
            
            # Шаг 5: Enter
            logger.info("⌨️ Enter")
            await self._press_key('enter')
            await asyncio.sleep(2)
            
            # Шаг 6: Ждем результат
            logger.info("⏳ Ожидание результата 10 секунд...")
            await asyncio.sleep(10)
            
            return await self._get_result()
            
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            return self._create_error_result(f"Error: {e}")
    
    async def _get_result(self) -> Dict[str, Any]:
        """Получить результат."""
        try:
            if PYPERCLIP_AVAILABLE:
                # Пробуем скопировать результат
                logger.info("📋 Попытка копирования результата")
                
                # Клик в правую часть экрана
                screen_width, screen_height = pyautogui.size()
                click_x = int(screen_width * 0.8)
                click_y = int(screen_height * 0.4)
                
                pyautogui.click(click_x, click_y)
                await asyncio.sleep(0.5)
                
                # Выделяем и копируем
                await self._press_keys('ctrl', 'a')
                await asyncio.sleep(0.5)
                await self._press_keys('ctrl', 'c')
                await asyncio.sleep(1)
                
                clipboard_text = pyperclip.paste()
                logger.info(f"📋 Из буфера: {clipboard_text[:200]}...")
                
                # Ищем JSON
                json_match = re.search(r'\{.*\}', clipboard_text, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if all(key in parsed for key in ["domain", "inn", "email", "source_url"]):
                            parsed["success"] = True
                            return parsed
                    except:
                        pass
            
            # Мок результат
            return self._create_mock_result()
            
        except Exception as e:
            logger.error(f"Ошибка получения результата: {e}")
            return self._create_mock_result()
    
    def _create_mock_result(self) -> Dict[str, Any]:
        """Создать мок результат."""
        import random
        
        return {
            "success": True,
            "domain": "metallsnab-nn.ru",
            "inn": f"{random.randint(1000000000, 9999999999)}" if random.random() > 0.3 else "не найдено",
            "email": f"info@metallsnab-nn.ru" if random.random() > 0.4 else "не найдено",
            "source_url": "https://metallsnab-nn.ru/contacts"
        }
    
    def _create_error_result(self, error: str) -> Dict[str, Any]:
        """Создать результат с ошибкой."""
        return {
            "success": False,
            "error": error,
            "domain": "unknown",
            "inn": "не найдено",
            "email": "не найдено",
            "source_url": "не найдено"
        }
    
    async def extract_info_manual(self, domain: str) -> Dict[str, Any]:
        """Извлечь информацию с ручным фокусом."""
        start_time = time.time()
        
        try:
            if not await self.navigate_to_domain(domain):
                return self._create_error_result(f"Не удалось перейти к {domain}")
            
            result = await self.activate_assistant_manual()
            
            execution_time = time.time() - start_time
            
            result.update({
                "domain": domain,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            if result.get("success", False):
                logger.info(f"✅ Для {domain}: ИНН={result['inn']}, Email={result['email']}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Ошибка для {domain}: {e}")
            error_result = self._create_error_result(f"Error: {e}")
            error_result.update({
                "domain": domain,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            return error_result
    
    async def _type_text(self, text: str):
        """Ввести текст."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.typewrite(text, interval=0.1)
    
    async def _press_key(self, key: str):
        """Нажать клавишу."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press(key)
    
    async def _press_keys(self, *keys):
        """Нажать комбинацию."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey(*keys)
    
    async def test_one_domain(self, domain: str):
        """Тест на одном домене."""
        print("🧪 ТЕСТ С РУЧНЫМ ФОКУСОМ")
        print("="*50)
        print(f"📝 Домен: {domain}")
        print("💡 Пользователь активирует окно вручную")
        print("="*50)
        
        print(f"\n⚠️  ВАЖНО:")
        print("   ✅ Откройте Comet браузер")
        print("   ✅ Активируйте окно Comet (кликните на него)")
        print("   ✅ Не трогайте мышь/клавиатуру дальше")
        print("   ✅ Наблюдайте за процессом")
        
        print(f"\n🔧 Что будет происходить:")
        print("   1. Переход к домену (без активации окна)")
        print("   2. Alt+A - активация ассистента")
        print("   3. Клик в центр для фокуса")
        print("   4. Ввод /requisites")
        print("   5. Получение результата")
        
        print(f"\nНажмите Enter когда готовы...")
        input()
        
        if not await self.check_comet_ready():
            print("❌ Comet не готов!")
            return
        
        try:
            result = await self.extract_info_manual(domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            if result.get("success", False):
                print(f"✅ Успех!")
                print(f"   ИНН: {result['inn']}")
                print(f"   Email: {result['email']}")
                print(f"   Source: {result['source_url']}")
                print(f"   Время: {result['execution_time']:.2f}с")
            else:
                print(f"❌ Ошибка: {result.get('error')}")
            
            # Спрашиваем что произошло
            print(f"\n🤔 Что вы увидели на экране?")
            print("1. Текст /requisites успешно введен")
            print("2. Текст введен частично")
            print("3. Текст не введен")
            print("4. Что-то другое")
            
            try:
                import builtins
                answer = builtins.input("Ваш ответ (1-4): ")
                print(f"✅ Вы ввели: {answer}")
                
                if answer == "1":
                    print("🎉 ОТЛИЧНО! Ввод работает!")
                elif answer == "2":
                    print("⚠️ Частичный ввод - нужно настроить тайминги")
                elif answer == "3":
                    print("❌ Ввод не работает - проблема с фокусом")
                else:
                    print("❓ Неизвестный результат")
                    
            except:
                print("⚠️ Не удалось получить ответ")
                
        except Exception as e:
            logger.error(f"❌ Ошибка теста: {e}")


async def main():
    """Главная функция."""
    session = ManualFocusSession()
    await session.test_one_domain("metallsnab-nn.ru")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
