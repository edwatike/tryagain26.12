"""Скрипт для запуска парсера доменов."""
import asyncio
import json
from datetime import datetime
from parser import DomainInfoParser


async def main():
    """Основная функция."""
    print("="*70)
    print("🚀 DOMAIN INFO PARSER - Извлечение ИНН и Email")
    print("="*70)
    
    # Читаем список доменов
    domains_file = "../domains_list.txt"
    print(f"\n📂 Чтение доменов из: {domains_file}")
    
    try:
        with open(domains_file, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Файл {domains_file} не найден!")
        return
    
    print(f"✅ Загружено доменов: {len(domains)}")
    
    # Спрашиваем, сколько доменов парсить
    print(f"\n💡 Для теста рекомендуется начать с 5-10 доменов")
    try:
        limit_input = input(f"Сколько доменов парсить? (Enter = все {len(domains)}): ").strip()
        if limit_input:
            limit = int(limit_input)
            domains = domains[:limit]
    except (ValueError, KeyboardInterrupt):
        print("\n⚠️ Используем все домены")
    
    print(f"\n🎯 Будет обработано доменов: {len(domains)}")
    print(f"⏱️ Примерное время: {len(domains) * 10} секунд")
    
    # Создаем парсер
    parser = DomainInfoParser(headless=True, timeout=15000)
    
    try:
        # Запускаем браузер
        await parser.start()
        
        # Парсим домены
        print(f"\n{'='*70}")
        print("🔍 НАЧАЛО ПАРСИНГА")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        results = await parser.parse_domains(domains)
        end_time = datetime.now()
        
        # Статистика
        print(f"\n{'='*70}")
        print("📊 РЕЗУЛЬТАТЫ")
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
        
        # Детальные результаты
        print(f"\n{'='*70}")
        print("📝 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'='*70}\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['domain']}")
            if result['inn']:
                print(f"   ✅ ИНН: {result['inn']}")
            else:
                print(f"   ❌ ИНН: не найден")
            
            if result['emails']:
                print(f"   ✅ Email: {', '.join(result['emails'])}")
            else:
                print(f"   ❌ Email: не найден")
            
            if result['error']:
                print(f"   ⚠️ Ошибка: {result['error']}")
            
            print()
        
        # Сохраняем результаты в JSON
        output_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результаты сохранены в: {output_file}")
        
        # Сохраняем в CSV для удобства
        csv_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write("Domain,INN,Email,Source URLs,Error\n")
            for r in results:
                emails_str = "; ".join(r['emails']) if r['emails'] else ""
                urls_str = "; ".join(r['source_urls']) if r['source_urls'] else ""
                error_str = r['error'] if r['error'] else ""
                f.write(f'"{r["domain"]}","{r["inn"] or ""}","{emails_str}","{urls_str}","{error_str}"\n')
        
        print(f"💾 CSV сохранен в: {csv_file}")
        
        # Показываем успешные результаты
        print(f"\n{'='*70}")
        print("🎉 УСПЕШНЫЕ РЕЗУЛЬТАТЫ (ИНН + Email)")
        print(f"{'='*70}\n")
        
        successful = [r for r in results if r['inn'] and r['emails']]
        if successful:
            for r in successful:
                print(f"✅ {r['domain']}")
                print(f"   ИНН: {r['inn']}")
                print(f"   Email: {', '.join(r['emails'])}")
                print()
        else:
            print("⚠️ Нет результатов с обоими полями (ИНН и Email)")
        
    finally:
        # Закрываем браузер
        await parser.close()
    
    print(f"\n{'='*70}")
    print("✅ ПАРСИНГ ЗАВЕРШЕН")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
