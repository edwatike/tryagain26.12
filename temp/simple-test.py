import requests
import json

run_id = "29b8f6ca-91e1-4c3f-a703-8906ddd7241a"
base = "http://127.0.0.1:8000"

print("=" * 70)
print("ПРОВЕРКА СУЩЕСТВУЮЩЕГО PARSING RUN")
print("=" * 70)
print()

# Проверка parsing run
print("1. Parsing run:")
r = requests.get(f"{base}/parsing/runs/{run_id}")
run_data = r.json()
print(f"   Статус: {run_data.get('status')}")
print(f"   resultsCount: {run_data.get('resultsCount')}")
print()

# Проверка доменов
print("2. Домены через API:")
r = requests.get(f"{base}/domains/queue", params={"parsingRunId": run_id, "limit": 100})
domains_data = r.json()
count = len(domains_data.get("entries", []))
total = domains_data.get("total", 0)

print(f"   entries: {count}")
print(f"   total: {total}")

if count > 0:
    print()
    print("   ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
    print()
    print("   Первые 5 доменов:")
    for i, e in enumerate(domains_data["entries"][:5], 1):
        print(f"   {i}. {e.get('domain')}")
        print(f"      URL: {e.get('url')}")
        print(f"      parsingRunId: {e.get('parsingRunId')}")
        print()
    print("=" * 70)
    print("ВСЕ РАБОТАЕТ!")
    print("=" * 70)
    print()
    print(f"Откройте: http://localhost:3000/parsing-runs/{run_id}")
    print(f"Должны отображаться {count} доменов")
else:
    print()
    print("   ПРОБЛЕМА: Доменов нет!")
    print()
    print("   Response:")
    print(json.dumps(domains_data, indent=2, ensure_ascii=False))















