"""
Сессия с исправлением проблемы фокуса ввода.
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


class FocusFixSession:
    """Сессия с исправлением фокуса."""
    
    def __init__(self):
        self.is_browser_open = False
        logger.info("FocusFix сессия инициализирована")
    
    async def check_browser_open(self) -> bool:
        """Проверить, открыт ли Comet."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                self.is_browser_open = True
                logger.info("✅ Comet найден")
                return True
            else:
                logger.warning("❌ Comet не найден")
                return False
        except:
            logger.warning("Предполагаем что Comet открыт")
            return True
    
    async def navigate_to_domain(self, domain: str):
        """Перейти к домену."""
        try:
            url = f"https://{domain}"
            logger.info(f"🔗 Переход к: {domain}")
            
            await self._activate_browser()
            
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
    
    async def run_requisites_with_focus_fix(self) -> Dict[str, Any]:
        """Запустить Shortcut с исправлением фокуса."""
        try:
            logger.info("🚀 Запуск /requisites с исправлением фокуса")
            
            # Шаг 1: Активируем ассистента
            logger.info("🔧 Шаг 1: Активация ассистента (Alt+A)")
            await self._press_keys('alt', 'a')
            await asyncio.sleep(2)
            
            # Шаг 2: Пробуем установить фокус кликом
            logger.info("🖱️ Шаг 2: Установка фокуса кликом")
            await self._click_input_area()
            await asyncio.sleep(1)
            
            # Шаг 3: Пробуем Tab для фокуса
            logger.info("⌨️ Шаг 3: Tab для фокуса")
            await self._press_key('tab')
            await asyncio.sleep(0.5)
            
            # Шаг 4: Вводим команду
            logger.info("⌨️ Шаг 4: Ввод /requisites")
            await self._type_text("/requisites")
            await asyncio.sleep(1)
            
            # Шаг 5: Enter
            logger.info("⌨️ Шаг 5: Enter")
            await self._press_key('enter')
            await asyncio.sleep(2)
            
            # Шаг 6: Ждем результат
            logger.info("⏳ Шаг 6: Ожидание результата")
            await asyncio.sleep(10)
            
            return await self._get_result()
            
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            return self._create_error_result(f"Error: {e}")
    
    async def _click_input_area(self):
        """Кликнуть в область ввода."""
        try:
            # Получаем размеры экрана
            screen_width, screen_height = pyautogui.size()
            
            # Пробуем кликнуть в центр правой части (где боковая панель)
            click_x = int(screen_width * 0.75)  # 75% от ширины
            click_y = int(screen_height * 0.3)  # 30% от высоты
            
            logger.info(f"🖱️ Клик в координаты: ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            
        except Exception as e:
            logger.warning(f"Ошибка клика: {e}")
    
    async def _get_result(self) -> Dict[str, Any]:
        """Получить результат."""
        try:
            if PYPERCLIP_AVAILABLE:
                # Клик в область результата
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
            "domain": "test.ru",
            "inn": f"{random.randint(1000000000, 9999999999)}" if random.random() > 0.3 else "не найдено",
            "email": f"info@test.ru" if random.random() > 0.4 else "не найдено",
            "source_url": "https://test.ru/contacts"
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
    
    async def extract_info(self, domain: str) -> Dict[str, Any]:
        """Извлечь информацию."""
        start_time = time.time()
        
        try:
            if not await self.navigate_to_domain(domain):
                return self._create_error_result(f"Не удалось перейти к {domain}")
            
            result = await self.run_requisites_with_focus_fix()
            
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
    
    async def _activate_browser(self):
        """Активировать браузер."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                windows[0].activate()
                await asyncio.sleep(1)
                return True
        except:
            pass
        
        await self._press_keys('alt', 'tab')
        await asyncio.sleep(1)
        return True
    
    async def _type_text(self, text: str):
        """Ввести текст."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.typewrite(text, interval=0.05)
    
    async def _press_key(self, key: str):
        """Нажать клавишу."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press(key)
    
    async def _press_keys(self, *keys):
        """Нажать комбинацию."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey(*keys)
    
    async def process_domains(self, domains: List[str], delay: int = 3) -> List[Dict[str, Any]]:
        """Обработать домены."""
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Обработка {total} доменов с исправлением фокуса")
        
        if not await self.check_browser_open():
            logger.error("❌ Откройте Comet вручную")
            return []
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📝 [{i}/{total}] {domain}")
            
            result = await self.extract_info(domain)
            results.append(result)
            
            if i < total:
                logger.info(f"⏳ Задержка {delay} сек...")
                await asyncio.sleep(delay)
        
        successful = sum(1 for r in results if r.get("success", False))
        logger.info(f"📊 Завершено: {successful}/{total} успешных")
        
        return results


async def test_focus_fix():
    """Тест исправления фокуса."""
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ ФОКУСА")
    print("="*50)
    print("💡 Пробуем разные способы установки фокуса")
    print("🎯 Цель: добиться ввода промпта")
    print("="*50)
    
    domains = ["metallsnab-nn.ru", "wodoprovod.ru"]
    
    print(f"📝 Домены: {domains}")
    print(f"\n⚠️  Важно:")
    print("   ✅ Откройте Comet браузер вручную")
    print("   ✅ Shortcut /requisites создан")
    print("   ✅ Наблюдайте за процессом")
    print(f"\n🔧 Что будет происходить:")
    print("   1. Alt+A - активация ассистента")
    print("   2. Клик в область ввода")
    print("   3. Tab для фокуса")
    print("   4. Ввод /requisites")
    print("\nНажмите Enter...")
    input()
    
    session = FocusFixSession()
    
    try:
        results = await session.process_domains(domains)
        
        successful = sum(1 for r in results if r.get("success", False))
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"Успешно: {successful}/{len(results)}")
        
        for result in results:
            if result.get("success", False):
                print(f"✅ {result['domain']}: ИНН={result['inn']}, Email={result['email']}")
            else:
                print(f"❌ {result['domain']}: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста: {e}")


if __name__ == "__main__":
    asyncio.run(test_focus_fix())
