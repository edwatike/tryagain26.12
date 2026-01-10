"""
Быстрый тест фокуса - просто проверяет что Comet открывается и активируется.
"""
import time
import subprocess
from pathlib import Path

def quick_test():
    print("🚀 БЫСТРЫЙ ТЕСТ COMET")
    print("="*40)
    
    # 1. Найти Comet
    comet_paths = [
        Path(r"C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
        Path(r"C:\Program Files\Comet\Comet.exe"),
        Path(r"C:\Program Files (x86)\Comet\Comet.exe"),
        Path(r"C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe"),
        Path(r"C:\Users\admin\AppData\Local\Comet\Application\Comet.exe")
    ]
    
    comet_path = None
    for path in comet_paths:
        if path.exists():
            comet_path = str(path)
            print(f"✅ Найден Comet: {comet_path}")
            break
    
    if not comet_path:
        print("❌ Comet не найден!")
        return False
    
    # 2. Открыть Comet
    print("🚀 Открываю Comet...")
    subprocess.Popen([comet_path], shell=True)
    
    # 3. Ждем
    print("⏳ Жду 5 секунд...")
    time.sleep(5)
    
    # 4. Проверить окно
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'comet' in win.title.lower():
                    windows = [win]
                    break
        
        if windows:
            window = windows[0]
            print(f"✅ Найдено окно: {window.title}")
            print(f"📐 Размер: {window.width}x{window.height}")
            print(f"📍 Позиция: ({window.left}, {window.top})")
            
            # 5. Попробовать активировать
            try:
                window.activate()
                time.sleep(1)
                if window.isActive:
                    print("✅ Окно активно!")
                    return True
                else:
                    print("⚠️ Окно не стало активным")
                    return False
            except Exception as e:
                print(f"❌ Ошибка активации: {e}")
                return False
        else:
            print("❌ Окна Comet не найдены")
            return False
            
    except ImportError:
        print("❌ pygetwindow не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    
    if success:
        print("\n🎉 Тест успешен!")
        print("✅ Comet открыт и активен")
    else:
        print("\n❌ Тест не удался")
        print("💡 Нужно проверить установку Comet")
    
    print("\nНажмите Enter...")
    input()
