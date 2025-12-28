import requests
import time
import sys

BASE = "http://127.0.0.1:8000"

print("=" * 70)
print("ТЕСТ: СОЗДАНИЕ И ПРОВЕРКА PARSING RUN")
print("=" * 70)
print()

# 1. Создание
print("1. Создание parsing run...")
try:
    r = requests.post(f"{BASE}/parsing/start", json={"keyword": "фланец", "depth": 1, "source": "google"}, timeout=10)
    r.raise_for_status()
    data = r.json()
    run_id = data["runId"]
    print(f"   ✅ Создан: {run_id}")
    print(f"   Статус: {data['status']}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

print()

# 2. Ожидание
print("2. Ожидание завершения (90 секунд)...")
completed = False
for i in range(18):
    time.sleep(5)
    try:
        r = requests.get(f"{BASE}/parsing/status/{run_id}", timeout=5)
        r.raise_for_status()
        status = r.json()["status"]
        print(f"   [{i*5+5}с] {status}")
        if status == "completed":
            completed = True
            print("   ✅ Парсинг завершен!")
            break
        elif status == "failed":
            print(f"   ❌ Ошибка парсинга")
            sys.exit(1)
    except Exception as e:
        print(f"   ⚠️  Ошибка: {e}")

if not completed:
    print("   ⚠️  Не завершился за 90 сек")

print()

# 3. Проверка доменов
print("3. Проверка доменов через API...")
try:
    r = requests.get(f"{BASE}/domains/queue", params={"parsingRunId": run_id, "limit": 100}, timeout=10)
    r.raise_for_status()
    d = r.json()
    count = len(d.get("entries", []))
    total = d.get("total", 0)
    
    print(f"   entries: {count}")
    print(f"   total: {total}")
    
    if count > 0:
        print()
        print("   ✅✅✅ ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
        print()
        print("   Первые 5 доменов:")
        for i, e in enumerate(d["entries"][:5], 1):
            print(f"   {i}. {e.get('domain')}")
            print(f"      URL: {e.get('url')}")
            print(f"      parsingRunId: {e.get('parsingRunId')}")
            print()
        
        print("=" * 70)
        print("✅✅✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!")
        print("=" * 70)
        print()
        print(f"Откройте в браузере: http://localhost:3000/parsing-runs/{run_id}")
        print(f"Должны отображаться {count} доменов")
        sys.exit(0)
    else:
        print()
        print("   ❌ ПРОБЛЕМА: Доменов нет!")
        print(f"   Response: {d}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



