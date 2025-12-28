#!/usr/bin/env python3
"""Быстрая проверка проблемы."""
import requests
import json

run_id = "29b8f6ca-91e1-4c3f-a703-8906ddd7241a"
BASE = "http://127.0.0.1:8000"

print("Проверка доменов для run_id:", run_id)
print()

# Проверка через API
try:
    r = requests.get(f"{BASE}/domains/queue", params={"parsingRunId": run_id, "limit": 100}, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        count = len(data.get("entries", []))
        total = data.get("total", 0)
        print(f"Entries: {count}, Total: {total}")
        
        if count > 0:
            print("\n✅ ДОКАЗАТЕЛЬСТВО - API возвращает домены:")
            for i, e in enumerate(data["entries"][:5], 1):
                print(f"  {i}. {e.get('domain')} - {e.get('url')}")
                print(f"     parsingRunId: {e.get('parsingRunId')}")
        else:
            print("\n❌ Доменов нет!")
            print("Response:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"Error: {r.text[:200]}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()



