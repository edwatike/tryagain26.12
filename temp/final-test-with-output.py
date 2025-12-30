#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Финальный тест с выводом результата в файл."""
import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_FILE = "temp/test-result.txt"

def log(msg):
    """Логирование с выводом в консоль и файл."""
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def main():
    # Очистить файл результата
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("=== ФИНАЛЬНЫЙ ТЕСТ ===\n\n")
    
    log("=" * 70)
    log("ФИНАЛЬНЫЙ ТЕСТ: СОЗДАНИЕ PARSING RUN И ПРОВЕРКА РЕЗУЛЬТАТОВ")
    log("=" * 70)
    log("")
    
    # 1. Создание parsing run
    log("1. Создание parsing run...")
    try:
        r = requests.post(
            f"{BASE_URL}/parsing/start",
            json={"keyword": "фланец", "depth": 1, "source": "google"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        run_id = data["runId"]
        log(f"   ✅ Создан: {run_id}")
        log(f"   Статус: {data['status']}")
    except Exception as e:
        log(f"   ❌ Ошибка: {e}")
        return 1
    
    log("")
    
    # 2. Ожидание завершения
    log("2. Ожидание завершения парсинга (90 секунд)...")
    completed = False
    for i in range(18):
        time.sleep(5)
        try:
            r = requests.get(f"{BASE_URL}/parsing/status/{run_id}", timeout=5)
            r.raise_for_status()
            status_data = r.json()
            status = status_data["status"]
            log(f"   [{i*5+5}с] Статус: {status}")
            
            if status == "completed":
                log("   ✅ Парсинг завершен!")
                completed = True
                break
            elif status == "failed":
                log(f"   ❌ Ошибка: {status_data.get('error', 'Unknown')}")
                return 1
        except Exception as e:
            log(f"   ⚠️  Ошибка проверки статуса: {e}")
    
    if not completed:
        log("   ⚠️  Парсинг не завершился за 90 секунд, продолжаю проверку...")
    
    log("")
    
    # 3. Проверка доменов
    log("3. Проверка доменов через API:")
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
        
        log(f"   ✅ Ответ получен:")
        log(f"      entries: {entries_count}")
        log(f"      total: {total}")
        
        if entries_count > 0:
            log("")
            log("   ✅✅✅ ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
            log("")
            log("   Первые 5 доменов:")
            for i, entry in enumerate(domains_data["entries"][:5], 1):
                log(f"   {i}. {entry.get('domain')}")
                log(f"      URL: {entry.get('url')}")
                log(f"      parsingRunId: {entry.get('parsingRunId')}")
                log("")
            
            log("=" * 70)
            log("✅✅✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!")
            log("=" * 70)
            log("")
            log(f"Откройте в браузере: http://localhost:3000/parsing-runs/{run_id}")
            log(f"Должны отображаться {entries_count} доменов")
            return 0
        else:
            log("")
            log("   ❌ ПРОБЛЕМА: API не возвращает домены!")
            log("   Response structure:")
            log(json.dumps(domains_data, indent=2, ensure_ascii=False)[:500])
            return 1
            
    except Exception as e:
        log(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())









