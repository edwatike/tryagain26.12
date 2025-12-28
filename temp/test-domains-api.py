#!/usr/bin/env python3
"""Тестовый скрипт для проверки API domains/queue."""
import requests
import json
import sys

def test_domains_api(run_id: str):
    """Тестирует API domains/queue для конкретного parsing run."""
    base_url = "http://127.0.0.1:8000"
    
    print(f"=== Тестирование API для run_id: {run_id} ===\n")
    
    # 1. Проверка parsing run
    print("1. Проверка parsing run:")
    try:
        run_response = requests.get(f"{base_url}/parsing/runs/{run_id}")
        run_response.raise_for_status()
        run_data = run_response.json()
        print(f"   ✅ Статус: {run_data.get('status')}")
        print(f"   ✅ resultsCount: {run_data.get('resultsCount')}")
        print(f"   ✅ keyword: {run_data.get('keyword')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    print()
    
    # 2. Проверка domains/queue
    print("2. Проверка domains/queue:")
    try:
        domains_response = requests.get(
            f"{base_url}/domains/queue",
            params={"parsingRunId": run_id, "limit": 100}
        )
        domains_response.raise_for_status()
        domains_data = domains_response.json()
        
        entries_count = len(domains_data.get('entries', []))
        total = domains_data.get('total', 0)
        
        print(f"   ✅ entries: {entries_count}")
        print(f"   ✅ total: {total}")
        print(f"   ✅ limit: {domains_data.get('limit')}")
        print(f"   ✅ offset: {domains_data.get('offset')}")
        
        if entries_count > 0:
            print(f"\n   Первые 3 домена:")
            for i, entry in enumerate(domains_data.get('entries', [])[:3], 1):
                print(f"   {i}. {entry.get('domain')} - {entry.get('url')}")
            print(f"\n   ✅✅✅ API РАБОТАЕТ! Домены возвращаются!" -ForegroundColor Green)
            return True
        else:
            if total > 0:
                print(f"\n   ⚠️  ПРОБЛЕМА: API вернул total={total}, но entries пустой!")
            else:
                print(f"\n   ⚠️  Нет доменов для этого parsing run")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        if hasattr(e, 'response'):
            print(f"   Статус: {e.response.status_code}")
            try:
                print(f"   Ответ: {e.response.json()}")
            except:
                print(f"   Текст: {e.response.text[:200]}")
        return False

if __name__ == "__main__":
    # Тестируем конкретный run_id
    test_run_id = "22709d9d-3f12-4a29-b9e0-f3ca6bb7a159"
    
    if len(sys.argv) > 1:
        test_run_id = sys.argv[1]
    
    success = test_domains_api(test_run_id)
    sys.exit(0 if success else 1)



