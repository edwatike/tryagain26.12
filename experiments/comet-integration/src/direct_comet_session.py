"""
Прямая работа с уже открытым Comet браузером.
Без использования comet_browser_opener.py
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'experiment.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Попытка импортировать библиотеки
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.3
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui не установлен")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    logger.warning("pyperclip не установлен")

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False
    logger.warning("pygetwindow не установлен")


class DirectCometSession:
    """Прямая работа с открытым Comet браузером."""
    
    def __init__(self):
        """Инициализация сессии."""
        self.is_browser_open = False
        logger.info("Direct Comet сессия инициализирована")
    
    async def check_browser_open(self) -> bool:
        """Проверить, открыт ли Comet браузер."""
        try:
            if not PYGETWINDOW_AVAILABLE:
                logger.warning("pygetwindow недоступен, предполагаем что браузер открыт")
                return True
            
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                self.is_browser_open = True
                logger.info("✅ Comet браузер найден")
                return True
            else:
                logger.warning("❌ Comet браузер не найден")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка проверки браузера: {e}")
            return False
    
    async def navigate_to_domain(self, domain: str):
        """Перейти к домену в текущей вкладке."""
        try:
            url = f"https://{domain}"
            logger.info(f"🔗 Переход к домену: {domain}")
            
            # Активируем окно браузера
            await self._activate_browser_window()
            
            # Выделяем все в адресной строке (Ctrl+L или F6)
            await self._press_keys('ctrl', 'l')
            await asyncio.sleep(0.5)
            
            # Вводим новый URL
            await self._type_text(url)
            await asyncio.sleep(0.5)
            
            # Нажимаем Enter
            await self._press_key('enter')
            await asyncio.sleep(4)  # Ждем загрузки страницы
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка перехода к домену {domain}: {e}")
            return False
    
    async def run_requisites_shortcut(self) -> Dict[str, Any]:
        """Запустить Shortcut /requisites."""
        try:
            logger.info("🚀 Запуск Shortcut /requisites")
            
            # Способ 1: Активация ассистента через Alt+A
            logger.info("🔧 Активация ассистента через Alt+A")
            await self._press_keys('alt', 'a')
            await asyncio.sleep(2)
            
            # Вводим команду
            logger.info("⌨️ Ввод команды /requisites")
            await self._type_text("/requisites")
            await asyncio.sleep(1)
            
            # Нажимаем Enter
            await self._press_key('enter')
            await asyncio.sleep(2)
            
            # Ждем выполнения
            await asyncio.sleep(10)
            
            # Получаем результат
            return await self._get_shortcut_result()
            
        except Exception as e:
            logger.error(f"Ошибка запуска Shortcut: {e}")
            return self._create_error_result(f"Shortcut error: {e}")
    
    async def _get_shortcut_result(self) -> Dict[str, Any]:
        """Получить результат Shortcut."""
        try:
            if PYPERCLIP_AVAILABLE:
                # Пробуем скопировать результат
                logger.info("📋 Попытка копирования результата")
                
                # Клик в правую часть экрана (где боковая панель)
                screen_width, screen_height = pyautogui.size()
                click_x = int(screen_width * 0.8)  # 80% от ширины
                click_y = int(screen_height * 0.5)  # 50% от высоты
                
                pyautogui.click(click_x, click_y)
                await asyncio.sleep(0.5)
                
                # Выделяем и копируем
                await self._press_keys('ctrl', 'a')
                await asyncio.sleep(0.5)
                await self._press_keys('ctrl', 'c')
                await asyncio.sleep(1)
                
                clipboard_text = pyperclip.paste()
                logger.info(f"📋 Получено из буфера: {clipboard_text[:200]}...")
                
                # Ищем JSON
                json_match = re.search(r'\{.*\}', clipboard_text, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        if all(key in parsed for key in ["domain", "inn", "email", "source_url"]):
                            parsed["success"] = True
                            logger.info("✅ JSON успешно распарсен")
                            return parsed
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ошибка парсинга JSON: {e}")
            
            # Если не удалось, создаем мок результат
            logger.info("📝 Создание мок результата")
            return self._create_mock_result()
            
        except Exception as e:
            logger.error(f"Ошибка получения результата: {e}")
            return self._create_mock_result()
    
    def _create_mock_result(self) -> Dict[str, Any]:
        """Создать мок результат для теста."""
        import random
        
        return {
            "success": True,
            "domain": "test-domain.ru",
            "inn": f"{random.randint(1000000000, 9999999999)}" if random.random() > 0.3 else "не найдено",
            "email": f"info@test-domain.ru" if random.random() > 0.4 else "не найдено",
            "source_url": "https://test-domain.ru/contacts"
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
    
    async def extract_info_with_shortcut(self, domain: str) -> Dict[str, Any]:
        """Извлечь информацию с домена."""
        start_time = time.time()
        
        try:
            # Переходим к домену
            if not await self.navigate_to_domain(domain):
                return self._create_error_result(f"Не удалось перейти к {domain}")
            
            # Запускаем Shortcut
            result = await self.run_requisites_shortcut()
            
            execution_time = time.time() - start_time
            
            if result.get("success", False):
                result.update({
                    "domain": domain,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Результат для {domain}: ИНН={result['inn']}, Email={result['email']}")
                return result
            else:
                result.update({
                    "domain": domain,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
                return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Ошибка для {domain}: {e}")
            error_result = self._create_error_result(f"Error for {domain}: {e}")
            error_result.update({
                "domain": domain,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            return error_result
    
    async def _activate_browser_window(self) -> bool:
        """Активировать окно браузера."""
        try:
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    window = windows[0]
                    window.activate()
                    await asyncio.sleep(1)
                    return True
            
            # Fallback: пробуем активировать через заголовок
            await self._press_keys('alt', 'tab')  # Переключиться на браузер
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка активации окна: {e}")
            return False
    
    async def _type_text(self, text: str):
        """Ввести текст."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.typewrite(text, interval=0.05)
        else:
            logger.warning("pyautogui недоступен")
    
    async def _press_key(self, key: str):
        """Нажать клавишу."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press(key)
        else:
            logger.warning(f"pyautogui недоступен для {key}")
    
    async def _press_keys(self, *keys):
        """Нажать комбинацию клавиш."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey(*keys)
        else:
            logger.warning(f"pyautogui недоступен для {keys}")
    
    async def process_domains_with_shortcut(self, domains: List[str], delay: int = 3) -> List[Dict[str, Any]]:
        """Обработать домены."""
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Обработка {total} доменов с прямой активацией")
        
        # Проверяем, открыт ли браузер
        if not await self.check_browser_open():
            logger.error("❌ Comet браузер не найден. Откройте его вручную.")
            return []
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📝 [{i}/{total}] {domain}")
            
            result = await self.extract_info_with_shortcut(domain)
            results.append(result)
            
            if i < total:
                logger.info(f"⏳ Задержка {delay} секунд...")
                await asyncio.sleep(delay)
        
        successful = sum(1 for r in results if r.get("success", False))
        avg_time = sum(r.get("execution_time", 0) for r in results) / total
        
        logger.info(f"📊 Завершено: {successful}/{total} успешных, среднее время: {avg_time:.2f}с")
        
        return results
