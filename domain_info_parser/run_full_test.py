"""Автоматический запуск парсера на всех доменах."""
import asyncio
import json
from datetime import datetime
from parser import DomainInfoParser


async def main():
    """Основная функция."""
    print("="*70)
    print("🚀 ПОЛНЫЙ ПАРСИНГ ВСЕХ ДОМЕНОВ")
    print("="*70)
    
    # Читаем список доменов
    domains_file = "../domains_list.txt"
    
    with open(domains_file, "r", encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip()]
    
    print(f"\n✅ Загружено доменов: {len(domains)}")
    print(f"⏱️ Примерное время: {len(domains) * 10 // 60} минут")
    
    # Создаем парсер
    parser = DomainInfoParser(headless=True, timeout=15000)
    
    try:
        await parser.start()
        
        print(f"\n{'='*70}")
        print("🔍 НАЧАЛО ПАРСИНГА")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        results = await parser.parse_domains(domains)
        end_time = datetime.now()
        
        # Статистика
        print(f"\n{'='*70}")
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*70}")
        
        total = len(results)
        with_inn = sum(1 for r in results if r['inn'])
        with_email = sum(1 for r in results if r['emails'])
        with_both = sum(1 for r in results if r['inn'] and r['emails'])
        with_errors = sum(1 for r in results if r['error'])
        
        print(f"\n✅ Обработано доменов: {total}")
        print(f"📋 Найден ИНН: {with_inn} ({with_inn/total*100:.1f}%)")
        print(f"📧 Найден Email: {with_email} ({with_email/total*100:.1f}%)")
        print(f"🎯 Найдено и ИНН и Email: {with_both} ({with_both/total*100:.1f}%)")
        print(f"❌ Ошибок: {with_errors} ({with_errors/total*100:.1f}%)")
        print(f"⏱️ Время выполнения: {(end_time - start_time).total_seconds():.1f} сек")
        
        # Сохраняем результаты
        output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: {output_file}")
        
        # CSV
        csv_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write("Domain,INN,Email,Source URLs,Error\n")
            for r in results:
                emails_str = "; ".join(r['emails']) if r['emails'] else ""
                urls_str = "; ".join(r['source_urls']) if r['source_urls'] else ""
                error_str = r['error'] if r['error'] else ""
                f.write(f'"{r["domain"]}","{r["inn"] or ""}","{emails_str}","{urls_str}","{error_str}"\n')
        
        print(f"💾 CSV сохранен в: {csv_file}")
        
        # Топ результаты
        print(f"\n{'='*70}")
        print("🏆 ТОП-10 УСПЕШНЫХ РЕЗУЛЬТАТОВ")
        print(f"{'='*70}\n")
        
        successful = [r for r in results if r['inn'] and r['emails']]
        for i, r in enumerate(successful[:10], 1):
            print(f"{i}. {r['domain']}")
            print(f"   ИНН: {r['inn']}")
            print(f"   Email: {', '.join(r['emails'])}")
            print()
        
        print(f"\n{'='*70}")
        print("✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"{'='*70}")
        
    finally:
        await parser.close()


if __name__ == "__main__":
    asyncio.run(main())
