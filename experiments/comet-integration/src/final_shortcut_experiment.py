"""
Финальный эксперимент с Enhanced Shortcut /requisites.
Реальное извлечение ИНН и email из буфера обмена!
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import List
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from enhanced_shortcut_session import EnhancedShortcutSession

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinalShortcutExperiment:
    """Финальный эксперимент с Enhanced Shortcut."""
    
    def __init__(self):
        self.comet_session = EnhancedShortcutSession()
        self.results = []
    
    async def run_experiment(self, domains: List[str], save_results: bool = True):
        """Запуск финального эксперимента."""
        logger.info(f"🚀 Запуск финального эксперимента с Enhanced Shortcut /requisites на {len(domains)} доменах")
        
        try:
            # Обрабатываем домены в одной сессии
            self.results = await self.comet_session.process_domains_with_shortcut(
                domains, 
                delay=4  # Задержка для надежности
            )
            
            # Анализируем результаты
            self.analyze_results()
            
            # Сохраняем результаты
            if save_results:
                self.save_results()
            
            logger.info("🎉 Финальный эксперимент с Shortcut завершен!")
            
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
        
        print("\n" + "="*80)
        print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА")
        print("🎯 Enhanced Shortcut /requisites + Real Clipboard Extraction")
        print("="*80)
        print(f"Всего доменов: {total}")
        print(f"Успешно: {successful} ({successful/total*100:.1f}%)")
        print(f"Неудачно: {failed} ({failed/total*100:.1f}%)")
        print(f"Среднее время: {avg_time:.2f} сек/домен")
        print("-"*80)
        print(f"ИНН найдено: {inn_found} ({inn_found/successful*100:.1f}% от успешных)")
        print(f"Email найдено: {email_found} ({email_found/successful*100:.1f}% от успешных)")
        print(f"ИНН+Email найдено: {both_found} ({both_found/successful*100:.1f}% от успешных)")
        print("="*80)
        
        # Показываем успешные результаты в нужном формате
        successful_results = [r for r in self.results if r.get("success", False)]
        if successful_results:
            print("\n🎯 НАЙДЕННЫЕ РЕКВИЗИТЫ (JSON формат):")
            print("-"*80)
            
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
        
        # Итоговая оценка
        print(f"\n🏆 ИТОГОВАЯ ОЦЕНКА:")
        if both_found >= 7:
            print("🎉 ОТЛИЧНО! Большинство доменов обработаны успешно")
        elif both_found >= 5:
            print("✅ ХОРОШО! Более половины доменов обработаны успешно")
        elif both_found >= 3:
            print("⚠️ УДОВЛЕТВОРИТЕЛЬНО! Нужна доработка")
        else:
            print("❌ ПОТРЕБУЕТСЯ УЛУЧШЕНИЕ")
    
    def save_results(self):
        """Сохранение результатов."""
        if not self.results:
            logger.warning("Нет результатов для сохранения")
            return
        
        # Сохраняем в JSON
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_shortcut_results_{timestamp}.json"
        output_path = Path(__file__).parent.parent / 'data' / filename
        
        stats = {
            "experiment_type": "final_enhanced_shortcut",
            "shortcut": "/requisites",
            "extraction_method": "clipboard",
            "total_domains": len(self.results),
            "successful": sum(1 for r in self.results if r.get("success", False)),
            "failed": sum(1 for r in self.results if not r.get("success", False)),
            "inn_found": sum(1 for r in self.results if r.get("inn", "не найдено") != "не найдено"),
            "email_found": sum(1 for r in self.results if r.get("email", "не найдено") != "не найдено"),
            "timestamp": datetime.now().isoformat(),
            "results": self.results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Полные результаты сохранены в: {output_path}")
        
        # Дополнительно сохраняем только успешные результаты в нужном формате
        successful_results = [r for r in self.results if r.get("success", False)]
        if successful_results:
            clean_filename = f"final_clean_results_{timestamp}.json"
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
            
            # Также создаем CSV для удобства
            import csv
            csv_filename = f"final_results_{timestamp}.csv"
            csv_output_path = Path(__file__).parent.parent / 'data' / csv_filename
            
            with open(csv_output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['domain', 'inn', 'email', 'source_url', 'execution_time', 'success'])
                
                for result in self.results:
                    writer.writerow([
                        result.get('domain', ''),
                        result.get('inn', ''),
                        result.get('email', ''),
                        result.get('source_url', ''),
                        result.get('execution_time', ''),
                        result.get('success', '')
                    ])
            
            logger.info(f"📁 CSV результаты сохранены в: {csv_output_path}")


async def main():
    """Главная функция."""
    experiment = FinalShortcutExperiment()
    
    print("🧪 FINAL ENHANCED SHORTCUT EXPERIMENT")
    print("="*80)
    print("💡 Финальный эксперимент с Enhanced Shortcut /requisites")
    print("🎯 Реальное извлечение ИНН и email из буфера обмена")
    print("="*80)
    
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
    
    print(f"\n⚠️  КРИТИЧЕСКИ ВАЖНО:")
    print("   ✅ Создан Shortcut /requisites в Comet")
    print("   ✅ Установлены pyautogui + pyperclip")
    print("   ✅ Comet браузер установлен и готов")
    print("   ✅ НЕ трогать мышь/клавиатуру 15-20 минут")
    print("   ✅ Программа будет копировать результаты из буфера обмена")
    print(f"\n🎯 Что нового:")
    print("   ✅ Реальное извлечение из буфера обмена")
    print("   ✅ Умный парсинг JSON и текста")
    print("   ✅ Автоматическое сохранение в JSON + CSV")
    print("   ✅ Детальная статистика и оценка качества")
    print(f"\n🏆 Ожидаемые результаты:")
    print("   📊 ИНН + email + source_url для каждого домена")
    print("   📁 Автоматическое сохранение в 3 форматах")
    print("   📈 Детальная статистика успешности")
    print("\nНажмите Enter для начала финального эксперимента...")
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
