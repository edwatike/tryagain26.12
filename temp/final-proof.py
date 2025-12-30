#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальный тест с доказательством работы."""
import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("=" * 70)
    print("ФИНАЛЬНЫЙ ТЕСТ С ДОКАЗАТЕЛЬСТВОМ")
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
        return 1
    
    print()
    
    # 2. Ожидание завершения
    print("2. Ожидание завершения (60 сек)...")
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
                return 1
        except:
            pass
    
    if not completed:
        print("   ⚠️  Не завершился, продолжаю...")
    
    print()
    
    # 3. Проверка доменов
    print("3. Проверка доменов через API:")
    try:
        r = requests.get(
            f"{BASE_URL}/domains/queue",
            params={"parsingRunId": run_id, "limit": 100},
            timeout=10
        )
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
            print("✅✅✅ ВСЕ РАБОТАЕТ!")
            print("=" * 70)
            print()
            print(f"Откройте: http://localhost:3000/parsing-runs/{run_id}")
            print(f"Должны отображаться {count} доменов")
            return 0
        else:
            print()
            print("   ❌ ПРОБЛЕМА: Доменов нет!")
            print("   Response:", json.dumps(d, indent=2, ensure_ascii=False)[:300])
            return 1
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())









