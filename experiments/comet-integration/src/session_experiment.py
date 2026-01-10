"""
Эксперимент с Comet Session - управление одной сессией браузера.
"""
import asyncio
import sys
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from comet_session import CometSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CometSessionExperiment:
    """Эксперимент с сессией Comet."""
    
    def __init__(self):
        self.comet_session = CometSession()
        self.results = []
    
    async def run_experiment(self, domains: List[str], save_results: bool = True):
        """
        Запуск эксперимента с сессией.
        
        Args:
            domains: Список доменов для обработки
            save_results: Сохранять ли результаты
        """
        logger.info(f"🚀 Запуск эксперимента с сессией на {len(domains)} доменах")
        
        try:
            # Обрабатываем домены в одной сессии
            self.results = await self.comet_session.process_domains(domains)
            
            # Анализируем результаты
            self.analyze_results()
            
            # Сохраняем результаты
            if save_results:
                self.save_results()
            
            logger.info("🎉 Эксперимент с сессией завершен!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в эксперименте: {e}")
        finally:
            # Закрываем браузер
            await self.comet_session.close_browser()
    
    def analyze_results(self):
        """Анализ результатов эксперимента."""
        if not self.results:
            logger.warning("Нет результатов для анализа")
            return
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        failed = total - successful
        
        # Анализ извлечения данных
        inn_found = sum(1 for r in self.results 
                        if r.get("success", False) and r.get("inn", "не найдено") != "не найдено")
        email_found = sum(1 for r in self.results 
                          if r.get("success", False) and r.get("email", "не найдено") != "не найдено")
        
        avg_time = sum(r.get("execution_time", 0) for r in self.results) / total
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА С СЕССИЕЙ")
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
        successful_results = [r for r in self.results if r.get("success", False)]
        if successful_results:
            print("\n🎯 ПРИМЕРЫ УСПЕШНЫХ ИЗВЛЕЧЕНИЙ:")
            for i, result in enumerate(successful_results[:3], 1):
                print(f"{i}. {result['domain']}")
                print(f"   ИНН: {result['inn']}")
                print(f"   Email: {result['email']}")
                print(f"   Компания: {result['company']}")
                print()
        
        # Показываем ошибки
        failed_results = [r for r in self.results if not r.get("success", False)]
        if failed_results:
            print("❌ ОШИБКИ:")
            for result in failed_results[:5]:
                print(f"   {result['domain']}: {result.get('error', 'Unknown error')}")
    
    def save_results(self):
        """Сохранение результатов."""
        if not self.results:
            logger.warning("Нет результатов для сохранения")
            return
        
        # Сохраняем в JSON
        from datetime import datetime
        import json
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_results_{timestamp}.json"
        output_path = Path(__file__).parent.parent / 'data' / filename
        
        stats = {
            "experiment_type": "comet_session",
            "total_domains": len(self.results),
            "successful": sum(1 for r in self.results if r.get("success", False)),
            "failed": sum(1 for r in self.results if not r.get("success", False)),
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Результаты сохранены в: {output_path}")
    
    def load_domains_from_file(self, file_path: str) -> List[str]:
        """Загрузка доменов из файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Загружено {len(domains)} доменов из файла: {file_path}")
            return domains
        except Exception as e:
            logger.error(f"Ошибка загрузки доменов: {e}")
            return []


async def main():
    """Главная функция."""
    experiment = CometSessionExperiment()
    
    print("🧪 Comet Session Experiment")
    print("="*50)
    print("💡 Этот эксперимент использует ОДНУ сессию браузера")
    print("💡 Браузер открывается один раз и переключается между доменами")
    print("="*50)
    
    # Тестовые домены
    test_domains = [
        "santech.ru",
        "lunda.ru", 
        "gremir.ru"
    ]
    
    # Пробуем загрузить из файла
    domains_file = Path("../data/sample_domains.txt")
    if domains_file.exists():
        domains = experiment.load_domains_from_file(str(domains_file))
        # Ограничиваем для теста
        domains = domains[:3]
    else:
        domains = test_domains
    
    print(f"📝 Будут обработаны домены: {domains}")
    print("\n⚠️  Важно: Убедитесь, что pyautogui установлен (pip install pyautogui)")
    print("⚠️  Не используйте мышь/клавиатуру во время эксперимента!")
    print("\nНажмите Enter для начала...")
    input()
    
    # Запускаем эксперимент
    await experiment.run_experiment(domains)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Эксперимент прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
