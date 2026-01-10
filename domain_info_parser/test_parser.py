"""Быстрый тест парсера на 5 доменах."""
import asyncio
import sys
from parser import DomainInfoParser


async def main():
    """Тестирование парсера."""
    # Тестовые домены из списка
    test_domains = [
        "kranikoff.ru",
        "santech.ru",
        "onyxspb.ru",
        "lunda.ru",
        "tehprommarket.ru"
    ]
    
    print("="*70)
    print("🧪 ТЕСТ ПАРСЕРА - 5 доменов")
    print("="*70)
    print(f"\nДомены для теста:")
    for i, domain in enumerate(test_domains, 1):
        print(f"{i}. {domain}")
    
    parser = DomainInfoParser(headless=True, timeout=15000)
    
    try:
        await parser.start()
        
        print(f"\n{'='*70}")
        print("🔍 НАЧАЛО ПАРСИНГА")
        print(f"{'='*70}\n")
        
        results = await parser.parse_domains(test_domains)
        
        # Статистика
        print(f"\n{'='*70}")
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА")
        print(f"{'='*70}\n")
        
        total = len(results)
        with_inn = sum(1 for r in results if r['inn'])
        with_email = sum(1 for r in results if r['emails'])
        with_both = sum(1 for r in results if r['inn'] and r['emails'])
        
        print(f"✅ Обработано: {total}")
        print(f"📋 ИНН найден: {with_inn} ({with_inn/total*100:.0f}%)")
        print(f"📧 Email найден: {with_email} ({with_email/total*100:.0f}%)")
        print(f"🎯 Оба поля: {with_both} ({with_both/total*100:.0f}%)")
        
        # Детали
        print(f"\n{'='*70}")
        print("📝 ДЕТАЛИ")
        print(f"{'='*70}\n")
        
        for i, r in enumerate(results, 1):
            status = "✅" if (r['inn'] and r['emails']) else "⚠️" if (r['inn'] or r['emails']) else "❌"
            print(f"{status} {i}. {r['domain']}")
            print(f"   ИНН: {r['inn'] or '❌ не найден'}")
            print(f"   Email: {', '.join(r['emails']) if r['emails'] else '❌ не найден'}")
            if r['error']:
                print(f"   Ошибка: {r['error']}")
            print()
        
        # Проверка успешности
        if with_both >= 2:
            print("🎉 ТЕСТ ПРОЙДЕН! Парсер работает корректно.")
            return 0
        else:
            print("⚠️ ТЕСТ НЕ ПРОЙДЕН! Найдено мало результатов.")
            return 1
            
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await parser.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
