#!/usr/bin/env python3
"""Проверка режима Chrome CDP - видимый или headless"""
import requests
import json

try:
    response = requests.get("http://127.0.0.1:9222/json/version", timeout=5)
    if response.status_code == 200:
        data = response.json()
        user_agent = data.get("User-Agent", "")
        browser = data.get("Browser", "")
        
        print("=" * 60)
        print("Chrome CDP Status:")
        print("=" * 60)
        print(f"Browser: {browser}")
        print(f"User-Agent: {user_agent}")
        print()
        
        if "HeadlessChrome" in user_agent:
            print("[ERROR] ПРОБЛЕМА: Chrome запущен в HEADLESS режиме!")
            print("   Парсер не сможет показать вам окно для решения CAPTCHA")
            print()
            print("РЕШЕНИЕ:")
            print("1. Закройте все окна Chrome")
            print("2. Запустите start-chrome.bat")
            print("3. Убедитесь, что Chrome открылся в видимом окне")
            print("4. Запустите этот скрипт снова для проверки")
        else:
            print("[OK] Chrome запущен в ВИДИМОМ режиме")
            print("   Парсер сможет показать вам окно для решения CAPTCHA")
        
        print()
        print(f"WebSocket URL: {data.get('webSocketDebuggerUrl', 'N/A')}")
        print("=" * 60)
    else:
        print(f"[ERROR] Chrome CDP вернул статус {response.status_code}")
        print("   Убедитесь, что Chrome запущен с --remote-debugging-port=9222")
except requests.exceptions.ConnectionError:
    print("[ERROR] Chrome CDP недоступен на порту 9222")
    print("   Запустите Chrome через start-chrome.bat")
except Exception as e:
    print(f"[ERROR] Ошибка: {e}")

