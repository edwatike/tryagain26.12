"""
Основной файл эксперимента по интеграции Comet Shortcuts.
Запускает извлечение контактной информации из доменов.
"""
import asyncio
import sys
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from comet_client import CometClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CometExperiment:
    """Класс для управления экспериментом."""
    
    def __init__(self):
        self.comet_client = CometClient()
        self.results = []
    
    async def run_experiment(self, domains: List[str], save_results: bool = True):
        """
        Запуск эксперимента на указанных доменах.
        
        Args:
            domains: Список доменов для обработки
            save_results: Сохранять ли результаты в файлы
        """
        logger.info(f"🚀 Запуск эксперимента на {len(domains)} доменах")
        
        # Проверяем соединение с Comet
        if not await self.comet_client.test_comet_connection():
            logger.error("❌ Comet недоступен. Эксперимент прерван.")
            return
        
        logger.info("✅ Comet доступен. Начинаем обработку доменов...")
        
        # Запускаем пакетную обработку
        self.results = await self.comet_client.batch_extract_company_info(domains)
        
        # Анализируем результаты
        self.analyze_results()
        
        # Сохраняем результаты
        if save_results:
            self.save_experiment_results()
        
        logger.info("🎉 Эксперимент завершен!")
    
    def analyze_results(self):
        """Анализ результатов эксперимента."""
        if not self.results:
            logger.warning("Нет результатов для анализа")
            return
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        failed = total - successful
        
        # Анализ извлечения ИНН
        inn_found = sum(1 for r in self.results 
                        if r.get("success", False) and r.get("inn", "не найдено") != "не найдено")
        
        # Анализ извлечения email
        email_found = sum(1 for r in self.results 
                          if r.get("success", False) and r.get("email", "не найдено") != "не найдено")
        
        # Анализ извлечения компании
        company_found = sum(1 for r in self.results 
                           if r.get("success", False) and r.get("company", "не найдено") != "не найдено")
        
        # Среднее время выполнения
        avg_time = sum(r.get("execution_time", 0) for r in self.results) / total
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА")
        print("="*60)
        print(f"Всего доменов: {total}")
        print(f"Успешно обработано: {successful} ({successful/total*100:.1f}%)")
        print(f"Неудачно: {failed} ({failed/total*100:.1f}%)")
        print(f"Среднее время: {avg_time:.2f} сек/домен")
        print("-"*60)
        print(f"ИНН найдено: {inn_found} ({inn_found/successful*100:.1f}% от успешных)")
        print(f"Email найдено: {email_found} ({email_found/successful*100:.1f}% от успешных)")
        print(f"Компании найдено: {company_found} ({company_found/successful*100:.1f}% от успешных)")
        print("="*60)
        
        # Показываем примеры успешных извлечений
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
            if len(failed_results) > 5:
                print(f"   ... и еще {len(failed_results) - 5} ошибок")
    
    def save_experiment_results(self):
        """Сохранение результатов эксперимента."""
        if not self.results:
            logger.warning("Нет результатов для сохранения")
            return
        
        # Сохраняем в JSON
        json_path = self.comet_client.save_results_to_json(self.results)
        
        # Сохраняем в CSV
        csv_path = self.comet_client.save_results_to_csv(self.results)
        
        logger.info(f"📁 Результаты сохранены:")
        logger.info(f"   JSON: {json_path}")
        logger.info(f"   CSV: {csv_path}")
    
    def load_domains_from_file(self, file_path: str) -> List[str]:
        """
        Загрузка доменов из файла.
        
        Args:
            file_path: Путь к файлу с доменами (один домен на строку)
            
        Returns:
            Список доменов
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            logger.info(f"Загружено {len(domains)} доменов из файла: {file_path}")
            return domains
        except Exception as e:
            logger.error(f"Ошибка загрузки доменов из файла: {e}")
            return []


async def main():
    """Главная функция эксперимента."""
    experiment = CometExperiment()
    
    print("🧪 Comet Integration Experiment")
    print("="*50)
    
    # Варианты тестовых доменов
    test_domains = [
        "santech.ru",
        "lunda.ru", 
        "gremir.ru",
        "metallsnab-nn.ru",
        "spb.lemanapro.ru"
    ]
    
    # Пробуем загрузить из файла, если нет - используем тестовые
    domains_file = Path("../data/sample_domains.txt")
    if domains_file.exists():
        domains = experiment.load_domains_from_file(str(domains_file))
    else:
        domains = test_domains
        logger.info(f"Используем тестовые домены: {domains}")
    
    # Запускаем эксперимент
    await experiment.run_experiment(domains)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Эксперимент прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в эксперименте: {e}")
        sys.exit(1)
