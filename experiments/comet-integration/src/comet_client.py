"""
Comet Shortcuts client для эксперимента по извлечению ИНН и email.
Изолированная версия для тестирования без интеграции в основной проект.
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


class CometClient:
    """Клиент для Comet Shortcuts интеграции."""
    
    def __init__(self, comet_script_path: str = None):
        """
        Инициализация Comet клиента.
        
        Args:
            comet_script_path: Путь к скрипту comet_browser_opener.py
        """
        if comet_script_path is None:
            # Ищем скрипт в temp папке основного проекта
            project_root = Path(__file__).parent.parent.parent.parent
            comet_script_path = project_root / "temp" / "comet_browser_opener.py"
        
        self.comet_script_path = Path(comet_script_path)
        if not self.comet_script_path.exists():
            raise FileNotFoundError(f"Comet script не найден: {self.comet_script_path}")
        
        logger.info(f"Comet клиент инициализирован с путем: {self.comet_script_path}")
    
    async def extract_company_info(self, domain: str, custom_prompt: str = None) -> Dict[str, Any]:
        """
        Извлечение информации о компании (ИНН, email) из домена используя Comet.
        
        Args:
            domain: Домен для анализа (например, "example.com")
            custom_prompt: Кастомный промпт для ассистента Comet (опционально)
            
        Returns:
            Словарь с извлеченной информацией
        """
        start_time = time.time()
        
        try:
            # Строим URL из домена
            url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            
            # Базовый промпт для извлечения ИНН и email
            default_prompt = (
                "Найди на этой странице: 1) ИНН компании, 2) email для закупок или контактов, "
                "3) название компании, 4) телефон. Если информации нет, укажи 'не найдено'. "
                "Верни результат в формате JSON: {'inn': '...', 'email': '...', 'company': '...', 'phone': '...'}"
            )
            
            prompt = custom_prompt or default_prompt
            
            logger.info(f"Запуск Comet извлечения для домена: {domain}")
            
            # Запускаем скрипт Comet с URL и промптом
            cmd = [
                sys.executable, 
                str(self.comet_script_path),
                url,
                prompt
            ]
            
            # Выполняем скрипт
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 минут таймаут
                cwd=str(self.comet_script_path.parent)
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"Comet скрипт завершился с ошибкой: {result.stderr}")
                return {
                    "success": False,
                    "error": "Comet script execution failed",
                    "details": result.stderr,
                    "domain": domain,
                    "execution_time": execution_time
                }
            
            # Парсим вывод (ответ ассистента Comet)
            output = result.stdout.strip()
            logger.info(f"Comet вывод для {domain} (время: {execution_time:.2f}с): {output[:200]}...")
            
            # Пытаемся извлечь JSON из вывода
            extracted_info = self._parse_comet_output(output)
            extracted_info.update({
                "domain": domain,
                "success": True,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return extracted_info
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"Comet извлечение превысило таймаут для домена: {domain}")
            return {
                "success": False,
                "error": "Timeout",
                "domain": domain,
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Ошибка в Comet извлечении для {domain}: {e}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain,
                "execution_time": execution_time
            }
    
    def _parse_comet_output(self, output: str) -> Dict[str, Any]:
        """
        Парсинг вывода Comet ассистента для извлечения структурированной информации.
        
        Args:
            output: Сырой вывод от Comet ассистента
            
        Returns:
            Словарь с извлеченной информацией
        """
        # Пытаемся найти JSON в выводе
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "inn": data.get("inn", "не найдено"),
                    "email": data.get("email", "не найдено"),
                    "company": data.get("company", "не найдено"),
                    "phone": data.get("phone", "не найдено"),
                    "raw_output": output
                }
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить JSON из вывода Comet: {json_match.group()}")
        
        # Fallback: пытаемся извлечь ИНН и email используя regex
        inn_match = re.search(r'ИНН[:\s]*(\d{10,})', output, re.IGNORECASE)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', output)
        company_match = re.search(r'компания[:\s]*([^\n\r]+)', output, re.IGNORECASE)
        phone_match = re.search(r'телефон[:\s]*([^\n\r]+)', output, re.IGNORECASE)
        
        return {
            "inn": inn_match.group(1) if inn_match else "не найдено",
            "email": email_match.group(0) if email_match else "не найдено",
            "company": company_match.group(1).strip() if company_match else "не найдено",
            "phone": phone_match.group(1).strip() if phone_match else "не найдено",
            "raw_output": output
        }
    
    async def batch_extract_company_info(self, domains: List[str], custom_prompt: str = None, delay: int = 2) -> List[Dict[str, Any]]:
        """
        Извлечение информации о компании для нескольких доменов.
        
        Args:
            domains: Список доменов для анализа
            custom_prompt: Кастомный промпт для ассистента Comet (опционально)
            delay: Задержка между запросами в секундах
            
        Returns:
            Список словарей с извлеченной информацией
        """
        results = []
        total_domains = len(domains)
        
        logger.info(f"Начало пакетной обработки {total_domains} доменов")
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"Обработка домена {i}/{total_domains}: {domain}")
            
            result = await self.extract_company_info(domain, custom_prompt)
            results.append(result)
            
            # Добавляем задержку между запросами чтобы не перегружать Comet
            if i < total_domains:  # Не ждем после последнего домена
                logger.info(f"Задержка {delay} секунд перед следующим доменом...")
                await asyncio.sleep(delay)
        
        # Статистика
        successful = sum(1 for r in results if r.get("success", False))
        failed = total_domains - successful
        avg_time = sum(r.get("execution_time", 0) for r in results) / total_domains
        
        logger.info(f"Пакетная обработка завершена: {successful} успешных, {failed} неудачных, среднее время: {avg_time:.2f}с")
        
        return results
    
    async def test_comet_connection(self) -> bool:
        """
        Проверка доступности браузера Comet.
        
        Returns:
            True если Comet работает, False в противном случае
        """
        try:
            logger.info("Проверка соединения с Comet...")
            result = await self.extract_company_info("google.com", "привет")
            is_working = result["success"] or "Comet script execution failed" not in result.get("error", "")
            logger.info(f"Comet соединение: {'работает' if is_working else 'не работает'}")
            return is_working
        except Exception as e:
            logger.error(f"Проверка соединения с Comet не удалась: {e}")
            return False
    
    def save_results_to_json(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Сохранение результатов в JSON файл.
        
        Args:
            results: Список результатов извлечения
            filename: Имя файла (опционально)
            
        Returns:
            Путь к сохраненному файлу
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comet_results_{timestamp}.json"
        
        output_path = Path(__file__).parent.parent / 'data' / filename
        
        # Добавляем статистику
        stats = {
            "total_domains": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Результаты сохранены в: {output_path}")
        return str(output_path)
    
    def save_results_to_csv(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Сохранение результатов в CSV файл.
        
        Args:
            results: Список результатов извлечения
            filename: Имя файла (опционально)
            
        Returns:
            Путь к сохраненному файлу
        """
        import csv
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comet_results_{timestamp}.csv"
        
        output_path = Path(__file__).parent.parent / 'data' / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Заголовки
            writer.writerow([
                'domain', 'success', 'inn', 'email', 'company', 'phone', 
                'execution_time', 'timestamp', 'error'
            ])
            
            # Данные
            for result in results:
                writer.writerow([
                    result.get('domain', ''),
                    result.get('success', ''),
                    result.get('inn', ''),
                    result.get('email', ''),
                    result.get('company', ''),
                    result.get('phone', ''),
                    result.get('execution_time', ''),
                    result.get('timestamp', ''),
                    result.get('error', '')
                ])
        
        logger.info(f"Результаты сохранены в CSV: {output_path}")
        return str(output_path)
