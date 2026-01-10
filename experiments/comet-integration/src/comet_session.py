"""
Comet Session - управление одной сессией браузера для обработки доменов.
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


class CometSession:
    """Управление одной сессией Comet браузера."""
    
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
        logger.info(f"Comet сессия инициализирована с путем: {self.comet_script_path}")
    
    async def open_browser(self, first_domain: str = "google.com"):
        """
        Открыть Comet браузер с первым доменом.
        
        Args:
            first_domain: Первый домен для открытия
        """
        try:
            if not PYAUTOGUI_AVAILABLE:
                raise ImportError("pyautogui необходим для автоматизации")
            
            logger.info(f"Открытие Comet браузера с доменом: {first_domain}")
            
            # Запускаем скрипт для открытия первого домена
            cmd = [
                sys.executable, 
                str(self.comet_script_path),
                f"https://{first_domain}",
                "привет"
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
                logger.info("✅ Comet браузер успешно открыт")
                
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
            logger.info(f"Переход к домену: {domain}")
            
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
            await asyncio.sleep(3)  # Ждем загрузки страницы
            
            # Активируем ассистента
            await self._activate_assistant()
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка перехода к домену {domain}: {e}")
            return False
    
    async def extract_info_from_domain(self, domain: str, prompt: str = None) -> Dict[str, Any]:
        """
        Извлечь информацию с домена.
        
        Args:
            domain: Домен для анализа
            prompt: Промпт для ассистента
            
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
            
            # Отправляем промпт ассистенту
            if prompt is None:
                prompt = (
                    "Найди на этой странице: 1) ИНН компании, 2) email для закупок или контактов, "
                    "3) название компании, 4) телефон. Если информации нет, укажи 'не найдено'. "
                    "Верни результат в формате JSON: {'inn': '...', 'email': '...', 'company': '...', 'phone': '...'}"
                )
            
            logger.info(f"Отправка промпта для домена: {domain}")
            await self._type_text(prompt)
            await asyncio.sleep(1)
            await self._press_key('enter')
            
            # Ждем ответа ассистента
            await asyncio.sleep(10)
            
            # Получаем ответ ассистента
            response = await self._get_assistant_response()
            
            execution_time = time.time() - start_time
            
            # Парсим ответ
            parsed_info = self._parse_response(response)
            parsed_info.update({
                "domain": domain,
                "success": True,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "raw_response": response
            })
            
            logger.info(f"✅ Информация извлечена для {domain} за {execution_time:.2f}с")
            return parsed_info
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Ошибка извлечения информации для {domain}: {e}")
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
    
    async def _get_assistant_response(self) -> str:
        """Получить ответ ассистента (простая реализация)."""
        # В реальной реализации здесь нужно было бы распознавать текст с экрана
        # или получать ответ через API Comet. Для эксперимента вернем заглушку.
        return "ИНН: 1234567890, Email: info@company.com, Company: Тестовая компания, Phone: +71234567890"
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Распарсить ответ ассистента."""
        # Пытаемся найти JSON в ответе
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "inn": data.get("inn", "не найдено"),
                    "email": data.get("email", "не найдено"),
                    "company": data.get("company", "не найдено"),
                    "phone": data.get("phone", "не найдено")
                }
            except json.JSONDecodeError:
                logger.warning("Не удалось распарсить JSON из ответа")
        
        # Fallback: извлекаем через regex
        inn_match = re.search(r'ИНН[:\s]*(\d{10,})', response, re.IGNORECASE)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', response)
        
        return {
            "inn": inn_match.group(1) if inn_match else "не найдено",
            "email": email_match.group(0) if email_match else "не найдено",
            "company": "не найдено",
            "phone": "не найдено"
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
            "company": "не найдено",
            "phone": "не найдено"
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
    
    async def process_domains(self, domains: List[str], delay: int = 3) -> List[Dict[str, Any]]:
        """
        Обработать список доменов.
        
        Args:
            domains: Список доменов для обработки
            delay: Задержка между доменами в секундах
            
        Returns:
            Список результатов
        """
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Начало обработки {total} доменов")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📝 Обработка домена {i}/{total}: {domain}")
            
            result = await self.extract_info_from_domain(domain)
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
    
    async def process_domains_with_prompt(self, domains: List[str], prompt: str, delay: int = 3) -> List[Dict[str, Any]]:
        """
        Обработать список доменов с кастомным промптом.
        
        Args:
            domains: Список доменов для обработки
            prompt: Кастомный промпт для ассистента
            delay: Задержка между доменами в секундах
            
        Returns:
            Список результатов
        """
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Начало обработки {total} доменов с кастомным промптом")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📝 Обработка домена {i}/{total}: {domain}")
            
            result = await self.extract_info_from_domain(domain, prompt)
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
