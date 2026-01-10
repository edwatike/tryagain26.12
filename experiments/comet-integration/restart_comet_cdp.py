"""
ПЕРЕЗАПУСК COMET С CDP
"""
import subprocess
import time
import requests
from pathlib import Path

def restart_comet_with_cdp():
    """Перезапустить Comet с CDP."""
    print("🚀 ПЕРЕЗАПУСК COMET С CDP")
    print("="*50)
    
    comet_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'Perplexity' / 'Comet' / 'Application' / 'comet.exe'
    
    if not comet_path.exists():
        print(f"❌ Comet не найден: {comet_path}")
        return False
    
    print(f"📍 Путь к Comet: {comet_path}")
    
    # Закрываем существующий Comet
    print("📍 Закрываю существующий Comet...")
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'comet.exe'], 
                      capture_output=True, timeout=10)
        time.sleep(3)
        print("✅ Comet закрыт")
    except:
        print("⚠️ Comet не был запущен или не удалось закрыть")
    
    # Запускаем Comet с CDP
    print("📍 Запускаю Comet с CDP...")
    cmd = [
        str(comet_path),
        '--remote-debugging-port=9222',
        '--remote-debugging-address=127.0.0.1',
        '--user-data-dir=./comet-temp-profile',
        '--no-first-run'
    ]
    
    try:
        process = subprocess.Popen(cmd, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        print("✅ Comet запущен с CDP!")
        print(f"📍 Команда: {' '.join(cmd)}")
        
        # Ждем запуска
        print("⏳ Ожидаю запуск CDP...")
        for i in range(30):
            time.sleep(1)
            try:
                response = requests.get("http://127.0.0.1:9222/json", timeout=2)
                if response.status_code == 200:
                    print(f"✅ CDP доступен через {i+1} секунд!")
                    targets = response.json()
                    print(f"📍 Найдено целей: {len(targets)}")
                    return True
            except:
                pass
            
            if (i + 1) % 5 == 0:
                print(f"   ⏳ Проверка {i+1}/30...")
        
        print("❌ CDP не стал доступен за 30 секунд")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

def main():
    """Главная функция."""
    print("🚀 ПЕРЕЗАПУСК COMET С CDP")
    print("="*30)
    print("📍 Закроет существующий Comet")
    print("📍 Запустит новый с CDP")
    print("📍 Проверит доступность CDP")
    print("="*30)
    
    if restart_comet_with_cdp():
        print("\n✅ УСПЕХ! Comet запущен с CDP!")
        print("🎯 Теперь можно запускать основной тест")
        print("📁 CDP доступен на: http://127.0.0.1:9222/json")
    else:
        print("\n❌ НЕУДАЧА! Не удалось запустить CDP")
    
    print("\n📍 Нажмите Enter для выхода...")
    input()

if __name__ == "__main__":
    import os
    main()
