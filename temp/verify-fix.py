#!/usr/bin/env python3
"""Простая проверка: создание parsing run и проверка доменов."""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("ПРОВЕРКА ИСПРАВЛЕНИЯ")
print("=" * 60)
print()

# 1. Проверка Backend
print("1. Проверка Backend...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    if r.status_code == 200:
        print("   ✅ Backend доступен")
    else:
        print(f"   ❌ Backend вернул {r.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Backend не доступен: {e}")
    exit(1)

# 2. Создание parsing run
print("\n2. Создание parsing run...")
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
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    exit(1)

# 3. Ожидание завершения
print("\n3. Ожидание завершения (60 сек)...")
completed = False
for i in range(12):
    time.sleep(5)
    try:
        r = requests.get(f"{BASE_URL}/parsing/status/{run_id}", timeout=5)
        r.raise_for_status()
        status = r.json()["status"]
        print(f"   [{i*5+5}с] {status}")
        if status == "completed":
            completed = True
            break
        elif status == "failed":
            print(f"   ❌ Ошибка парсинга")
            exit(1)
    except Exception as e:
        print(f"   Ошибка: {e}")

if not completed:
    print("   ⚠️  Не завершился за 60 сек")
    exit(1)

# 4. Проверка доменов
print("\n4. Проверка доменов...")
try:
    r = requests.get(
        f"{BASE_URL}/domains/queue",
        params={"parsingRunId": run_id, "limit": 100},
        timeout=10
    )
    r.raise_for_status()
    data = r.json()
    count = len(data.get("entries", []))
    total = data.get("total", 0)
    print(f"   ✅ Получено: {count} доменов (total: {total})")
    
    if count > 0:
        print("\n   Первые 3:")
        for i, e in enumerate(data["entries"][:3], 1):
            print(f"   {i}. {e.get('domain')} - {e.get('url')}")
        print(f"\n✅✅✅ ИСПРАВЛЕНИЕ РАБОТАЕТ!")
        print(f"\nОткройте: http://localhost:3000/parsing-runs/{run_id}")
        print(f"Должны отображаться {count} доменов")
    else:
        print("   ❌ Доменов нет!")
        exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО")
print("=" * 60)



