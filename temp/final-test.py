#!/usr/bin/env python3
"""Финальный тест: создание parsing run, ожидание завершения, проверка доменов."""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("ФИНАЛЬНЫЙ ТЕСТ: СОЗДАНИЕ ПARSING RUN И ПРОВЕРКА РЕЗУЛЬТАТОВ")
print("=" * 70)
print()

# 1. Создание parsing run
print("1. Создание parsing run...")
try:
    r = requests.post(
        f"{BASE_URL}/parsing/start",
        json={"keyword": "фланец", "depth": 1, "source": "google"},
        timeout=10
    )
    r.raise_for_status()
    data = r.json()
    run_id = data["runId"]
    print(f"   ✅ Создан: {run_id}")
    print(f"   Статус: {data['status']}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

print()

# 2. Ожидание завершения
print("2. Ожидание завершения парсинга (60 секунд)...")
completed = False
for i in range(12):
    time.sleep(5)
    try:
        r = requests.get(f"{BASE_URL}/parsing/status/{run_id}", timeout=5)
        r.raise_for_status()
        status_data = r.json()
        status = status_data["status"]
        print(f"   [{i*5+5}с] Статус: {status}", end="")
        
        if status == "completed":
            print(" ✅")
            completed = True
            break
        elif status == "failed":
            print(f" ❌")
            print(f"   Ошибка: {status_data.get('error', 'Unknown')}")
            exit(1)
        else:
            print()
    except Exception as e:
        print(f"   Ошибка: {e}")

if not completed:
    print("   ⚠️  Не завершился за 60 сек, продолжаю проверку...")

print()

# 3. Проверка parsing run
print("3. Проверка parsing run через API:")
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

# 4. Проверка доменов через API
print("4. Проверка доменов через API:")
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
    
    print(f"   ✅ Ответ получен:")
    print(f"      entries: {entries_count}")
    print(f"      total: {total}")
    print(f"      limit: {domains_data.get('limit')}")
    print(f"      offset: {domains_data.get('offset')}")
    
    if entries_count > 0:
        print(f"\n   ✅✅✅ ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
        print(f"\n   Первые 5 доменов:")
        for i, entry in enumerate(domains_data["entries"][:5], 1):
            print(f"   {i}. {entry.get('domain')}")
            print(f"      URL: {entry.get('url')}")
            print(f"      parsingRunId: {entry.get('parsingRunId')}")
            print(f"      keyword: {entry.get('keyword')}")
            print()
        
        print("=" * 70)
        print("✅✅✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!")
        print("=" * 70)
        print()
        print(f"Откройте в браузере: http://localhost:3000/parsing-runs/{run_id}")
        print(f"Должны отображаться {entries_count} доменов")
        print()
        print("Если домены не отображаются на фронтенде:")
        print("  1. Откройте консоль браузера (F12)")
        print("  2. Проверьте Network tab - запрос к /domains/queue")
        print("  3. Проверьте логи в консоли")
    else:
        print(f"\n   ❌ ПРОБЛЕМА: API не возвращает домены!")
        print(f"   Response structure:")
        print(json.dumps(domains_data, indent=2, ensure_ascii=False)[:500])
        exit(1)
        
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    exit(1)









