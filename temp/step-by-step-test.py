#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time
import sys
import io

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "http://127.0.0.1:8000"

print("=" * 70)
print("ШАГ ЗА ШАГОМ ТЕСТ")
print("=" * 70)
print()

# Шаг 1
print("ШАГ 1: Создание parsing run")
try:
    r = requests.post(f"{BASE}/parsing/start", json={"keyword": "фланец", "depth": 1, "source": "google"}, timeout=10)
    r.raise_for_status()
    run_id = r.json()["runId"]
    print(f"[OK] Run ID: {run_id}")
except Exception as e:
    print(f"[ERROR] Ошибка создания: {e}")
    sys.exit(1)
print()

# Шаг 2
print("ШАГ 2: Ожидание завершения (90 секунд)")
completed = False
for i in range(18):
    time.sleep(5)
    try:
        status = requests.get(f"{BASE}/parsing/status/{run_id}", timeout=5).json()["status"]
        print(f"   [{i*5+5}с] {status}")
        if status == "completed":
            print("   [OK] Завершен!")
            completed = True
            break
        elif status == "failed":
            print("   [ERROR] Ошибка!")
            break
    except Exception as e:
        print(f"   [WARNING] Ошибка проверки: {e}")
print()

# Шаг 3
print("ШАГ 3: Проверка доменов")
try:
    d = requests.get(f"{BASE}/domains/queue", params={"parsingRunId": run_id, "limit": 100}, timeout=10).json()
    count = len(d.get("entries", []))
    total = d.get("total", 0)
    print(f"   Доменов: {count}")
    print(f"   Total: {total}")
    print()

    if count > 0:
        print("=" * 70)
        print("[SUCCESS] ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
        print("=" * 70)
        print()
        print("Первые 5 доменов:")
        for i, e in enumerate(d["entries"][:5], 1):
            print(f"   {i}. {e.get('domain')}")
            print(f"      URL: {e.get('url')}")
            print(f"      parsingRunId: {e.get('parsingRunId')}")
            print()
        print("=" * 70)
        print("[SUCCESS] ВСЕ РАБОТАЕТ!")
        print("=" * 70)
        print()
        print(f"Откройте: http://localhost:3000/parsing-runs/{run_id}")
        print(f"Должны отображаться {count} доменов")
        sys.exit(0)
    else:
        print("[ERROR] ПРОБЛЕМА: Доменов нет!")
        print(f"Response: {d}")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] Ошибка получения доменов: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

