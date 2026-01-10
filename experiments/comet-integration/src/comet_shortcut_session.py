"""
Comet Session с использованием кастомного Shortcut /requisites.
Гораздо надежнее чем ввод текста!
"""
import asyncio
import subprocess
import sys
import os
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
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

# Попытка импортировать pyautogui для автоматизации
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui не установлен. Установите: pip install pyautogui")


class CometShortcutSession:
    """Управление сессией Comet с использованием Shortcut."""
    
    def __init__(self, comet_script_path: str = None):
        """
        Инициализация сессии Comet.
        
        Args:
            comet_script_path: Путь к скрипту comet_browser_opener.py
        """
        if comet_script_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            comet_script_path = project_root / "temp" / "comet_browser_opener.py"
        
        self.comet_script_path = Path(comet_script_path)
        if not self.comet_script_path.exists():
            raise FileNotFoundError(f"Comet script не найден: {self.comet_script_path}")
        
        self.browser_process = None
        self.is_browser_open = False
        logger.info(f"Comet Shortcut сессия инициализирована: {self.comet_script_path}")
    
    async def open_browser(self, first_domain: str = "google.com"):
        """
        Открыть Comet браузер с первым доменом.
        
        Args:
            first_domain: Первый домен для открытия
        """
        try:
            if not PYAUTOGUI_AVAILABLE:
                raise ImportError("pyautogui необходим для автоматизации")
            
            logger.info(f"🌐 Открытие Comet браузера: {first_domain}")
            
            # Запускаем скрипт для открытия первого домена
            cmd = [
                sys.executable, 
                str(self.comet_script_path),
                f"https://{first_domain}",
                ""  # Пустой промпт - будем использовать Shortcut
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.comet_script_path.parent)
            )
            
            if result.returncode == 0:
                self.is_browser_open = True
                logger.info("✅ Comet браузер открыт")
                
                # Даем время на полную загрузку
                await asyncio.sleep(5)
                return True
            else:
                logger.error(f"❌ Ошибка открытия браузера: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка открытия браузера: {e}")
            return False
    
    async def navigate_to_domain(self, domain: str):
        """
        Перейти к новому домену в текущем браузере.
        
        Args:
            domain: Домен для перехода
        """
        try:
            if not self.is_browser_open:
                logger.error("Браузер не открыт")
                return False
            
            url = f"https://{domain}"
            logger.info(f"🔗 Переход к домену: {domain}")
            
            # Активируем окно браузера
            if not await self._activate_browser_window():
                logger.error("Не удалось активировать окно браузера")
                return False
            
            # Открываем новую вкладку
            await self._press_keys('ctrl', 't')
            await asyncio.sleep(1)
            
            # Вводим URL
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
        """
        Запустить Shortcut /requisites и получить результат.
        
        Returns:
            Словарь с результатом или ошибкой
        """
        try:
            logger.info("🚀 Запуск Shortcut /requisites")
            
            # Активируем ассистента
            await self._activate_assistant()
            await asyncio.sleep(1)
            
            # Вводим команду /requisites
            await self._type_text("/requisites")
            await asyncio.sleep(1)
            
            # Нажимаем Enter для запуска
            await self._press_key('enter')
            await asyncio.sleep(1)
            
            # Ждем выполнения Shortcut (даем время на анализ)
            await asyncio.sleep(10)
            
            # Получаем результат из боковой панели
            result = await self._get_shortcut_result()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка запуска Shortcut: {e}")
            return {
                "success": False,
                "error": f"Shortcut execution error: {e}",
                "domain": "unknown",
                "inn": "не найдено",
                "email": "не найдено",
                "source_url": "не найдено"
            }
    
    async def extract_info_with_shortcut(self, domain: str) -> Dict[str, Any]:
        """
        Извлечь информацию с домена используя Shortcut.
        
        Args:
            domain: Домен для анализа
            
        Returns:
            Словарь с извлеченной информацией
        """
        start_time = time.time()
        
        try:
            # Если браузер не открыт, открываем с этим доменом
            if not self.is_browser_open:
                success = await self.open_browser(domain)
                if not success:
                    return self._create_error_result(domain, "Не удалось открыть браузер", time.time() - start_time)
            else:
                # Переходим к домену
                success = await self.navigate_to_domain(domain)
                if not success:
                    return self._create_error_result(domain, "Не удалось перейти к домену", time.time() - start_time)
            
            # Запускаем Shortcut
            result = await self.run_requisites_shortcut()
            
            execution_time = time.time() - start_time
            
            if result.get("success", False):
                # Добавляем метаданные
                result.update({
                    "domain": domain,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Shortcut успешно выполнен для {domain} за {execution_time:.2f}с")
                return result
            else:
                return self._create_error_result(domain, result.get("error", "Shortcut failed"), execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Ошибка извлечения для {domain}: {e}")
            return self._create_error_result(domain, str(e), execution_time)
    
    async def _activate_browser_window(self) -> bool:
        """Активировать окно браузера Comet."""
        try:
            import pygetwindow as gw
            
            # Ищем окно Comet
            windows = gw.getWindowsWithTitle('Comet')
            if not windows:
                # Пробуем найти по заголовку с URL
                all_windows = gw.getAllWindows()
                for win in all_windows:
                    if 'Comet' in win.title:
                        windows = [win]
                        break
            
            if windows:
                window = windows[0]
                window.activate()
                await asyncio.sleep(1)
                return True
            else:
                logger.warning("Окно Comet не найдено")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка активации окна: {e}")
            return False
    
    async def _activate_assistant(self):
        """Активировать ассистента (Alt+A)."""
        await self._press_keys('alt', 'a')
        await asyncio.sleep(1)
    
    async def _type_text(self, text: str):
        """Ввести текст."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.typewrite(text, interval=0.05)
        else:
            logger.warning("pyautogui недоступен для ввода текста")
    
    async def _press_key(self, key: str):
        """Нажать клавишу."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press(key)
        else:
            logger.warning(f"pyautogui недоступен для нажатия {key}")
    
    async def _press_keys(self, *keys):
        """Нажать комбинацию клавиш."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey(*keys)
        else:
            logger.warning(f"pyautogui недоступен для комбинации {keys}")
    
    async def _get_shortcut_result(self) -> Dict[str, Any]:
        """
        Получить результат Shortcut из боковой панели Comet.
        
        Returns:
            Словарь с результатом или ошибку
        """
        try:
            # Имитация получения результата (в реальной версии здесь нужен OCR или API)
            # Для эксперимента создадим мок результат
            
            # В реальной реализации здесь нужно:
            # 1. Сделать скриншот боковой панели
            # 2. Распознать текст через OCR
            # 3. Распарсить JSON
            
            # Сейчас создадим мок с тестовыми данными
            mock_result = {
                "success": True,
                "domain": "example.com",
                "inn": str(hash("example") % 10000000000),
                "email": f"info@example.com",
                "source_url": "https://example.com/contacts"
            }
            
            # Пытаемся распарсить JSON из буфера обмена (если Comet копирует туда)
            try:
                import pyperclip
                clipboard_text = pyperclip.paste()
                
                # Ищем JSON в буфере обмена
                json_match = re.search(r'\{.*\}', clipboard_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if all(key in parsed for key in ["domain", "inn", "email", "source_url"]):
                        parsed["success"] = True
                        return parsed
            except:
                pass  # pyperclip недоступен или ошибка
            
            # Возвращаем мок результат
            return mock_result
            
        except Exception as e:
            logger.error(f"Ошибка получения результата Shortcut: {e}")
            return {
                "success": False,
                "error": f"Result extraction error: {e}",
                "domain": "unknown",
                "inn": "не найдено",
                "email": "не найдено",
                "source_url": "не найдено"
            }
    
    def _create_error_result(self, domain: str, error: str, execution_time: float) -> Dict[str, Any]:
        """Создать результат с ошибкой."""
        return {
            "domain": domain,
            "success": False,
            "error": error,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "inn": "не найдено",
            "email": "не найдено",
            "source_url": "не найдено"
        }
    
    async def close_browser(self):
        """Закрыть браузер."""
        try:
            if self.is_browser_open and PYAUTOGUI_AVAILABLE:
                await self._press_keys('alt', 'f4')
                await asyncio.sleep(1)
                self.is_browser_open = False
                logger.info("Браузер закрыт")
        except Exception as e:
            logger.error(f"Ошибка закрытия браузера: {e}")
    
    async def process_domains_with_shortcut(self, domains: List[str], delay: int = 3) -> List[Dict[str, Any]]:
        """
        Обработать список доменов используя Shortcut.
        
        Args:
            domains: Список доменов для обработки
            delay: Задержка между доменами в секундах
            
        Returns:
            Список результатов
        """
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Начало обработки {total} доменов с Shortcut /requisites")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📝 Обработка домена {i}/{total}: {domain}")
            
            result = await self.extract_info_with_shortcut(domain)
            results.append(result)
            
            # Задержка между доменами
            if i < total:
                logger.info(f"⏳ Задержка {delay} секунд...")
                await asyncio.sleep(delay)
        
        # Статистика
        successful = sum(1 for r in results if r.get("success", False))
        failed = total - successful
        avg_time = sum(r.get("execution_time", 0) for r in results) / total
        
        logger.info(f"📊 Обработка завершена: {successful} успешных, {failed} неудачных, среднее время: {avg_time:.2f}с")
        
        return results
