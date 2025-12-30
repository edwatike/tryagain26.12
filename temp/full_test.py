#!/usr/bin/env python3
"""Полный тест: запуск сервисов, создание parsing run, проверка результатов через фронтенд API."""
import requests
import time
import json
import sys
import subprocess
import os

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"
PARSER_URL = "http://127.0.0.1:9003"

def check_service(url, name, max_attempts=20):
    """Проверяет доступность сервиса."""
    for i in range(max_attempts):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} доступен")
                return True
        except:
            pass
        if i < max_attempts - 1:
            time.sleep(3)
            print(f"⏳ Ожидание {name}... ({i+1}/{max_attempts})")
    print(f"❌ {name} не доступен")
    return False

def main():
    print("=" * 60)
    print("ПОЛНЫЙ ТЕСТ: Парсинг и отображение результатов")
    print("=" * 60)
    print()
    
    # 1. Проверка сервисов
    print("1. Проверка доступности сервисов...")
    backend_ok = check_service(f"{BASE_URL}/health", "Backend")
    parser_ok = check_service(f"{PARSER_URL}/health", "Parser Service")
    frontend_ok = check_service(f"{FRONTEND_URL}", "Frontend")
    
    if not (backend_ok and parser_ok and frontend_ok):
        print("\n❌ Не все сервисы доступны!")
        return 1
    
    print()
    
    # 2. Создание parsing run
    print("2. Создание parsing run...")
    try:
        response = requests.post(
            f"{BASE_URL}/parsing/start",
            json={"keyword": "фланец", "depth": 1, "source": "google"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        run_id = data["runId"]
        print(f"✅ Parsing run создан: {run_id}")
        print(f"   Статус: {data['status']}")
    except Exception as e:
        print(f"❌ Ошибка создания parsing run: {e}")
        return 1
    
    print()
    
    # 3. Ожидание завершения
    print("3. Ожидание завершения парсинга (максимум 2 минуты)...")
    completed = False
    for i in range(24):  # 24 * 5 = 120 секунд
        time.sleep(5)
        try:
            response = requests.get(f"{BASE_URL}/parsing/status/{run_id}", timeout=5)
            response.raise_for_status()
            status_data = response.json()
            status = status_data["status"]
            
            print(f"   [{i*5+5} сек] Статус: {status}", end="")
            
            if status == "completed":
                print(" ✅")
                completed = True
                break
            elif status == "failed":
                print(f" ❌")
                print(f"   Ошибка: {status_data.get('error', 'Unknown')}")
                return 1
            else:
                print()
        except Exception as e:
            print(f"   Ошибка проверки статуса: {e}")
    
    if not completed:
        print("\n⚠️  Парсинг не завершился за 2 минуты")
        return 1
    
    print()
    
    # 4. Проверка доменов через API
    print("4. Проверка доменов через API...")
    try:
        response = requests.get(
            f"{BASE_URL}/domains/queue",
            params={"parsingRunId": run_id, "limit": 100},
            timeout=10
        )
        response.raise_for_status()
        domains_data = response.json()
        
        entries_count = len(domains_data.get("entries", []))
        total = domains_data.get("total", 0)
        
        print(f"✅ API вернул: {entries_count} доменов (total: {total})")
        
        if entries_count > 0:
            print("\n   Первые 3 домена:")
            for i, entry in enumerate(domains_data.get("entries", [])[:3], 1):
                print(f"   {i}. {entry.get('domain')} - {entry.get('url')}")
            print("\n✅✅✅ ДОКАЗАТЕЛЬСТВО: API возвращает домены!")
        else:
            print("\n⚠️  Доменов нет в ответе API!")
            return 1
    except Exception as e:
        print(f"❌ Ошибка получения доменов: {e}")
        return 1
    
    print()
    
    # 5. Проверка parsing run через API (как фронтенд)
    print("5. Проверка parsing run через API (как фронтенд)...")
    try:
        response = requests.get(f"{BASE_URL}/parsing/runs/{run_id}", timeout=10)
        response.raise_for_status()
        run_data = response.json()
        
        print("✅ Parsing run данные:")
        print(f"   runId: {run_data.get('runId')}")
        print(f"   status: {run_data.get('status')}")
        print(f"   resultsCount: {run_data.get('resultsCount')}")
        print(f"   keyword: {run_data.get('keyword')}")
        
        if run_data.get("status") == "completed" and run_data.get("resultsCount", 0) > 0:
            print("\n✅✅✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!")
            print(f"\nОткройте в браузере: {FRONTEND_URL}/parsing-runs/{run_id}")
            print(f"Должны отображаться {run_data.get('resultsCount')} доменов")
            return 0
        else:
            print(f"\n⚠️  Статус: {run_data.get('status')}, resultsCount: {run_data.get('resultsCount')}")
            return 1
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())









