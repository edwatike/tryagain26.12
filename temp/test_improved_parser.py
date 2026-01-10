"""Тест улучшенного парсера ИНН на проблемных доменах."""
import asyncio
import sys
import os

# Добавляем путь к domain_info_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'domain_info_parser'))
from parser import DomainInfoParser

async def test_domains():
    parser = DomainInfoParser(headless=True, timeout=20000)
    await parser.start()
    
    test_domains = ['santech.ru', 'm-investspb.ru', 'mpstal.ru', 'vorder.ru']
    
    print("="*70)
    print("🧪 ТЕСТ УЛУЧШЕННОГО ПАРСЕРА ИНН")
    print("="*70)
    
    results = []
    for domain in test_domains:
        print(f'\n=== {domain} ===')
        result = await parser.parse_domain(domain)
        results.append(result)
        
        print(f'ИНН: {result.get("inn") or "❌ не найден"}')
        print(f'Email: {result.get("emails") or "❌ не найден"}')
        if result.get('error'):
            print(f'Ошибка: {result["error"]}')
    
    await parser.close()
    
    # Статистика
    print(f'\n{"="*70}')
    print("📊 РЕЗУЛЬТАТЫ")
    print(f'{"="*70}')
    
    total = len(results)
    with_inn = sum(1 for r in results if r['inn'])
    with_email = sum(1 for r in results if r['emails'])
    with_both = sum(1 for r in results if r['inn'] and r['emails'])
    
    print(f'\n✅ Обработано: {total}')
    print(f'📋 ИНН найден: {with_inn} ({with_inn/total*100:.0f}%)')
    print(f'📧 Email найден: {with_email} ({with_email/total*100:.0f}%)')
    print(f'🎯 Оба поля: {with_both} ({with_both/total*100:.0f}%)')
    
    if with_inn > 0:
        print('\n🎉 УЛУЧШЕНИЕ РАБОТАЕТ! Найдены ИНН на проблемных доменах.')
    else:
        print('\n⚠️ ИНН не найдены. Требуется дополнительная доработка.')

if __name__ == "__main__":
    asyncio.run(test_domains())
