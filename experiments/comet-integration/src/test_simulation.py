"""
Тест симуляции эксперимента без реального открытия браузера.
"""
import asyncio
import sys
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockCometSession:
    """Мок сессии Comet для тестирования без реального браузера."""
    
    def __init__(self):
        self.is_browser_open = False
        logger.info("🧪 Mock Comet сессия инициализирована")
    
    async def open_browser(self, first_domain: str = "google.com"):
        """Симуляция открытия браузера."""
        logger.info(f"🌐 Симуляция открытия браузера с доменом: {first_domain}")
        await asyncio.sleep(2)  # Симуляция времени открытия
        self.is_browser_open = True
        logger.info("✅ Браузер 'открыт'")
        return True
    
    async def navigate_to_domain(self, domain: str):
        """Симуляция перехода к домену."""
        logger.info(f"🔗 Симуляция перехода к домену: {domain}")
        await asyncio.sleep(1)  # Симуляция времени загрузки
        return True
    
    async def extract_info_from_domain(self, domain: str, prompt: str = None) -> dict:
        """Симуляция извлечения информации."""
        import time
        start_time = time.time()
        
        logger.info(f"🔍 Симуляция извлечения информации для: {domain}")
        
        # Симуляция процесса
        await self.navigate_to_domain(domain)
        await asyncio.sleep(2)  # Симуляция времени анализа
        
        execution_time = time.time() - start_time
        
        # Мок результаты (50% шанс найти ИНН, 40% шанс найти email)
        import random
        
        result = {
            "domain": domain,
            "success": True,
            "execution_time": execution_time,
            "timestamp": "2026-01-04T17:41:00",
            "inn": f"{random.randint(1000000000, 9999999999)}" if random.random() > 0.5 else "не найдено",
            "email": f"info@{domain}" if random.random() > 0.6 else "не найдено",
            "company": f"Компания {domain.replace('.', ' ').title()}" if random.random() > 0.4 else "не найдено",
            "phone": f"+7{random.randint(9000000000, 9999999999)}" if random.random() > 0.7 else "не найдено"
        }
        
        logger.info(f"✅ Информация 'извлечена' для {domain} за {execution_time:.2f}с")
        return result
    
    async def process_domains(self, domains: List[str], delay: int = 1) -> List[dict]:
        """Обработка доменов."""
        results = []
        total = len(domains)
        
        logger.info(f"🚀 Начало симуляции обработки {total} доменов")
        
        # Открываем браузер один раз
        await self.open_browser(domains[0] if domains else "google.com")
        
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
        
        logger.info(f"📊 Симуляция завершена: {successful} успешных, {failed} неудачных, среднее время: {avg_time:.2f}с")
        
        return results
    
    async def close_browser(self):
        """Симуляция закрытия браузера."""
        logger.info("🔄 Симуляция закрытия браузера")
        self.is_browser_open = False


async def run_simulation():
    """Запуск симуляции эксперимента."""
    print("🧪 Comet Session Simulation Test")
    print("="*50)
    print("💡 Это симуляция - реальный браузер не открывается")
    print("💡 Проверяется логика и время выполнения")
    print("="*50)
    
    # Тестовые домены
    test_domains = [
        "santech.ru",
        "lunda.ru", 
        "gremir.ru",
        "metallsnab-nn.ru",
        "spb.lemanapro.ru"
    ]
    
    print(f"📝 Тестовые домены: {test_domains}")
    print()
    
    # Создаем мок сессию
    session = MockCometSession()
    
    try:
        # Запускаем симуляцию
        results = await session.process_domains(test_domains, delay=1)
        
        # Анализируем результаты
        total = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        failed = total - successful
        
        inn_found = sum(1 for r in results 
                        if r.get("success", False) and r.get("inn", "не найдено") != "не найдено")
        email_found = sum(1 for r in results 
                          if r.get("success", False) and r.get("email", "не найдено") != "не найдено")
        
        avg_time = sum(r.get("execution_time", 0) for r in results) / total
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ СИМУЛЯЦИИ")
        print("="*60)
        print(f"Всего доменов: {total}")
        print(f"Успешно: {successful} ({successful/total*100:.1f}%)")
        print(f"Неудачно: {failed} ({failed/total*100:.1f}%)")
        print(f"Среднее время: {avg_time:.2f} сек/домен")
        print("-"*60)
        print(f"ИНН найдено: {inn_found} ({inn_found/successful*100:.1f}% от успешных)")
        print(f"Email найдено: {email_found} ({email_found/successful*100:.1f}% от успешных)")
        print("="*60)
        
        # Показываем примеры
        print("\n🎯 ПРИМЕРЫ РЕЗУЛЬТАТОВ:")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result['domain']}")
            print(f"   ИНН: {result['inn']}")
            print(f"   Email: {result['email']}")
            print(f"   Компания: {result['company']}")
            print()
        
        print("✅ Симуляция завершена успешно!")
        print("💡 Для реального теста используйте: run_session_experiment.bat")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в симуляции: {e}")
    finally:
        await session.close_browser()


if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("\n⚠️ Симуляция прервана пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
