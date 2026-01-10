"""
Эксперимент с использованием Shortcut /requisites в Comet.
Надежный способ извлечения ИНН и email!
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from comet_shortcut_session import CometShortcutSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShortcutExperiment:
    """Эксперимент с Shortcut /requisites."""
    
    def __init__(self):
        self.comet_session = CometShortcutSession()
        self.results = []
    
    async def run_experiment(self, domains: List[str], save_results: bool = True):
        """
        Запуск эксперимента с Shortcut.
        
        Args:
            domains: Список доменов для обработки
            save_results: Сохранять ли результаты
        """
        logger.info(f"🚀 Запуск эксперимента с Shortcut /requisites на {len(domains)} доменах")
        
        try:
            # Обрабатываем домены в одной сессии
            self.results = await self.comet_session.process_domains_with_shortcut(
                domains, 
                delay=4  # Увеличим задержку для надежности
            )
            
            # Анализируем результаты
            self.analyze_results()
            
            # Сохраняем результаты
            if save_results:
                self.save_results()
            
            logger.info("🎉 Эксперимент с Shortcut завершен!")
            
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
        both_found = sum(1 for r in self.results 
                         if r.get("success", False) 
                         and r.get("inn", "не найдено") != "не найдено" 
                         and r.get("email", "не найдено") != "не найдено")
        
        avg_time = sum(r.get("execution_time", 0) for r in self.results) / total
        
        print("\n" + "="*70)
        print("📊 РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА С SHORTCUT /REQUISITES")
        print("="*70)
        print(f"Всего доменов: {total}")
        print(f"Успешно: {successful} ({successful/total*100:.1f}%)")
        print(f"Неудачно: {failed} ({failed/total*100:.1f}%)")
        print(f"Среднее время: {avg_time:.2f} сек/домен")
        print("-"*70)
        print(f"ИНН найдено: {inn_found} ({inn_found/successful*100:.1f}% от успешных)")
        print(f"Email найдено: {email_found} ({email_found/successful*100:.1f}% от успешных)")
        print(f"ИНН+Email найдено: {both_found} ({both_found/successful*100:.1f}% от успешных)")
        print("="*70)
        
        # Показываем успешные результаты в нужном формате
        successful_results = [r for r in self.results if r.get("success", False)]
        if successful_results:
            print("\n🎯 НАЙДЕННЫЕ РЕКВИЗИТЫ (JSON формат):")
            print("-"*70)
            
            for i, result in enumerate(successful_results, 1):
                json_result = {
                    "domain": result['domain'],
                    "inn": result['inn'],
                    "email": result['email'],
                    "source_url": result.get('source_url', 'не указано')
                }
                print(f"{i}. {json.dumps(json_result, ensure_ascii=False, indent=2)}")
                print()
        
        # Показываем ошибки
        failed_results = [r for r in self.results if not r.get("success", False)]
        if failed_results:
            print("❌ ОШИБКИ:")
            for result in failed_results:
                print(f"   {result['domain']}: {result.get('error', 'Unknown error')}")
    
    def save_results(self):
        """Сохранение результатов."""
        if not self.results:
            logger.warning("Нет результатов для сохранения")
            return
        
        # Сохраняем в JSON
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shortcut_results_{timestamp}.json"
        output_path = Path(__file__).parent.parent / 'data' / filename
        
        stats = {
            "experiment_type": "shortcut_requisites",
            "shortcut": "/requisites",
            "total_domains": len(self.results),
            "successful": sum(1 for r in self.results if r.get("success", False)),
            "failed": sum(1 for r in self.results if not r.get("success", False)),
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Результаты сохранены в: {output_path}")
        
        # Дополнительно сохраняем только успешные результаты в нужном формате
        successful_results = [r for r in self.results if r.get("success", False)]
        if successful_results:
            clean_filename = f"shortcut_clean_results_{timestamp}.json"
            clean_output_path = Path(__file__).parent.parent / 'data' / clean_filename
            
            clean_results = []
            for result in successful_results:
                clean_results.append({
                    "domain": result['domain'],
                    "inn": result['inn'],
                    "email": result['email'],
                    "source_url": result.get('source_url', 'не указано')
                })
            
            with open(clean_output_path, 'w', encoding='utf-8') as f:
                json.dump(clean_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📁 Чистые результаты сохранены в: {clean_output_path}")


async def main():
    """Главная функция."""
    experiment = ShortcutExperiment()
    
    print("🧪 Shortcut /requisites Experiment")
    print("="*70)
    print("💡 Эксперимент с кастомным Shortcut в Comet")
    print("💡 Надежный способ извлечения ИНН и email")
    print("="*70)
    
    # Реальные домены из результатов парсинга
    real_domains = [
        "metallsnab-nn.ru",
        "wodoprovod.ru", 
        "ozon.ru",
        "gremir.ru",
        "spb.lemanapro.ru",
        "lunda.ru",
        "kranikoff.ru",
        "santech.ru",
        "onyxspb.ru",
        "tehprommarket.ru"
    ]
    
    print(f"📝 Домены для обработки ({len(real_domains)}):")
    for i, domain in enumerate(real_domains, 1):
        print(f"   {i}. {domain}")
    
    print(f"\n⚠️  Важно:")
    print("   ✅ Убедитесь, что Shortcut /requisites создан в Comet")
    print("   ✅ pyautogui установлен")
    print("   ✅ Comet браузер установлен и готов")
    print("   ✅ Не будете трогать мышь/клавиатуру 10-15 минут")
    print("   ✅ Программа будет автоматически запускать /requisites")
    print(f"\n🎯 Преимущества Shortcut:")
    print("   ✅ Надежность - не нужно вводить длинные промпты")
    print("   ✅ Скорость - готовая команда")
    print("   ✅ Точность - настроенный промпт")
    print("   ✅ Стабильность - меньше ошибок автоматизации")
    print("\nНажмите Enter для начала...")
    input()
    
    # Запускаем эксперимент
    await experiment.run_experiment(real_domains)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Эксперимент прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
