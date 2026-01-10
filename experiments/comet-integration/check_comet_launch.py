"""
ПРОВЕРКА ЗАПУСКА COMET
"""
import subprocess
import os
import sys
from pathlib import Path

def check_comet_path():
    """Проверить путь к Comet."""
    paths = [
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Perplexity' / 'Comet' / 'Application' / 'comet.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Perplexity' / 'Comet' / 'Application' / 'Comet.exe',
        Path('C:/Users/admin/AppData/Local/Perplexity/Comet/Application/comet.exe'),
        Path('C:/Users/admin/AppData/Local/Perplexity/Comet/Application/Comet.exe'),
        Path('C:/Program Files/Comet/comet.exe'),
        Path('C:/Program Files (x86)/Comet/comet.exe'),
    ]
    
    print("🔍 Проверка путей к Comet:")
    for i, path in enumerate(paths, 1):
        if path.exists():
            print(f"✅ Найден путь {i}: {path}")
            return path
        else:
            print(f"❌ Путь {i} не найден: {path}")
    
    return None

def test_comet_launch():
    """Тест запуска Comet."""
    print("🚀 ТЕСТ ЗАПУСКА COMET")
    print("="*50)
    
    comet_path = check_comet_path()
    if not comet_path:
        print("❌ Comet не найден!")
        return False
    
    print(f"\n📍 Найден Comet: {comet_path}")
    
    # Проверяем запущен ли уже
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq comet.exe'], 
                              capture_output=True, text=True, timeout=5)
        if 'comet.exe' in result.stdout.lower():
            print("✅ Comet уже запущен!")
            return True
    except:
        pass
    
    # Пробуем запустить без CDP
    print("📍 Пробую запустить Comet без CDP...")
    try:
        process = subprocess.Popen([str(comet_path)], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        print("✅ Comet запущен без CDP!")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска без CDP: {e}")
    
    # Пробуем запустить с CDP
    print("📍 Пробую запустить Comet с CDP...")
    cmd = [
        str(comet_path),
        '--remote-debugging-port=9222',
        '--remote-debugging-address=127.0.0.1',
        '--user-data-dir=./comet-temp-profile'
    ]
    
    try:
        process = subprocess.Popen(cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        print("✅ Comet запущен с CDP!")
        print(f"📍 Команда: {' '.join(cmd)}")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска с CDP: {e}")
    
    return False

def check_cdp():
    """Проверить CDP."""
    import requests
    
    try:
        response = requests.get("http://127.0.0.1:9222/json", timeout=5)
        if response.status_code == 200:
            print("✅ CDP доступен!")
            targets = response.json()
            print(f"📍 Найдено целей: {len(targets)}")
            for target in targets[:3]:  # Первые 3
                print(f"   - {target.get('title', 'Unknown')}: {target.get('url', 'No URL')}")
            return True
        else:
            print(f"❌ CDP вернул статус: {response.status_code}")
    except Exception as e:
        print(f"❌ CDP недоступен: {e}")
    
    return False

def main():
    """Главная функция."""
    print("🚀 ПРОВЕРКА ЗАПУСКА COMET")
    print("="*50)
    
    # Проверяем путь
    if not test_comet_launch():
        print("\n❌ НЕ УДАЛОСЬ ЗАПУСТИТЬ COMET!")
        return
    
    # Ждем и проверяем CDP
    import time
    print("\n⏳ Жду 10 секунд...")
    time.sleep(10)
    
    print("\n🔍 Проверяю CDP...")
    check_cdp()
    
    print("\n📊 РЕЗУЛЬТАТ:")
    print("="*20)
    print("✅ Проверьте запущен ли Comet")
    print("✅ Проверьте доступен ли http://127.0.0.1:9222/json")
    print("✅ Если все работает - можно запускать основной тест")

if __name__ == "__main__":
    main()
