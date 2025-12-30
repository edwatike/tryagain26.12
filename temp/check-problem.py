#!/usr/bin/env python3
"""Проверка проблемы с отображением результатов."""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
run_id = "29b8f6ca-91e1-4c3f-a703-8906ddd7241a"

print("=" * 60)
print("ПРОВЕРКА ПРОБЛЕМЫ С ОТОБРАЖЕНИЕМ РЕЗУЛЬТАТОВ")
print("=" * 60)
print()

# 1. Проверка parsing run
print("1. Проверка parsing run:")
try:
    r = requests.get(f"{BASE_URL}/parsing/runs/{run_id}", timeout=10)
    r.raise_for_status()
    run_data = r.json()
    print(f"   ✅ Статус: {run_data.get('status')}")
    print(f"   ✅ resultsCount: {run_data.get('resultsCount')}")
    print(f"   ✅ keyword: {run_data.get('keyword')}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

print()

# 2. Проверка доменов через API
print("2. Проверка доменов через API:")
try:
    r = requests.get(
        f"{BASE_URL}/domains/queue",
        params={"parsingRunId": run_id, "limit": 100},
        timeout=10
    )
    r.raise_for_status()
    domains_data = r.json()
    
    entries_count = len(domains_data.get("entries", []))
    total = domains_data.get("total", 0)
    
    print(f"   entries: {entries_count}")
    print(f"   total: {total}")
    
    if entries_count > 0:
        print(f"\n   ✅ API возвращает домены!")
        print(f"\n   Первые 3 домена:")
        for i, entry in enumerate(domains_data["entries"][:3], 1):
            print(f"   {i}. {entry.get('domain')} - {entry.get('url')}")
            print(f"      parsingRunId: {entry.get('parsingRunId')}")
    else:
        print(f"\n   ❌ API НЕ возвращает домены!")
        print(f"   Проверяю raw response...")
        print(f"   Response: {json.dumps(domains_data, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()

# 3. Проверка через фронтенд API (симуляция)
print("3. Симуляция запроса фронтенда:")
try:
    # Фронтенд вызывает getDomainsQueue с parsingRunId
    url = f"{BASE_URL}/domains/queue?parsingRunId={run_id}&limit=1000"
    print(f"   URL: {url}")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"   ✅ Ответ получен: {len(data.get('entries', []))} доменов")
    print(f"   Структура ответа:")
    print(f"     - entries: список из {len(data.get('entries', []))} элементов")
    print(f"     - total: {data.get('total')}")
    if len(data.get('entries', [])) > 0:
        first = data['entries'][0]
        print(f"   Первый элемент:")
        print(f"     - domain: {first.get('domain')}")
        print(f"     - url: {first.get('url')}")
        print(f"     - parsingRunId: {first.get('parsingRunId')}")
        print(f"     - keyword: {first.get('keyword')}")
        print(f"     - status: {first.get('status')}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)









