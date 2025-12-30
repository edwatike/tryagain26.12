import requests
import time

print("=== БЫСТРАЯ ПРОВЕРКА ===")
print()

# Создание
print("1. Создание...")
r = requests.post("http://127.0.0.1:8000/parsing/start", json={"keyword": "тест", "depth": 1, "source": "google"})
run_id = r.json()["runId"]
print(f"   Run ID: {run_id}")

# Ожидание
print()
print("2. Ожидание 60 сек...")
for i in range(12):
    time.sleep(5)
    status = requests.get(f"http://127.0.0.1:8000/parsing/status/{run_id}").json()["status"]
    print(f"   [{i*5+5}с] {status}")
    if status in ["completed", "failed"]:
        break

# Проверка
print()
print("3. Проверка доменов...")
d = requests.get("http://127.0.0.1:8000/domains/queue", params={"parsingRunId": run_id}).json()
count = len(d.get("entries", []))
print(f"   Доменов: {count}")

if count > 0:
    print()
    print("   ✅✅✅ ДОКАЗАТЕЛЬСТВО:")
    for i, e in enumerate(d["entries"][:5], 1):
        print(f"   {i}. {e.get('domain')} - {e.get('url')}")
    print()
    print(f"   Откройте: http://localhost:3000/parsing-runs/{run_id}")
    print()
    print("✅✅✅ ВСЕ РАБОТАЕТ!")
else:
    print("   ❌ Доменов нет!")









