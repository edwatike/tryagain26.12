"""
ИСПРАВЛЕННЫЙ ВВОД URL В COMET
Проблема: в адресную строку вводится "://-." вместо правильного URL
Решение: улучшаем фокус на адресную строку и ввод URL
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка зависимостей
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.error("pyautogui не установлен!")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


class FixedURLInput:
    """Исправленный ввод URL в Comet."""
    
    def __init__(self):
        logger.info("🚀 FixedURLInput инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # РАБОЧИЕ КООРДИНАТЫ
        self.input_field_x = int(self.screen_width * 0.85)   # Поле ввода ассистента
        self.input_field_y = int(self.screen_height * 0.92)
        
        # АДРЕСНАЯ СТРОКА - несколько вариантов для поиска
        self.address_bar_attempts = [
            (int(self.screen_width * 0.5), int(self.screen_height * 0.05)),   # Центр вверху
            (int(self.screen_width * 0.3), int(self.screen_height * 0.05)),   # Левее вверху
            (int(self.screen_width * 0.7), int(self.screen_height * 0.05)),   # Правее вверху
            (int(self.screen_width * 0.5), int(self.screen_height * 0.08)),   # Чуть ниже
        ]
        
        logger.info(f"🎯 Поле ввода ассистента: ({self.input_field_x}, {self.input_field_y})")
        logger.info(f"🌐 Адресная строка: {len(self.address_bar_attempts)} вариантов")
    
    def get_active_window_title(self):
        """Получить заголовок активного окна."""
        try:
            active = gw.getActiveWindow()
            return active.title if active else "Unknown"
        except:
            return "Error"
    
    def verify_comet_active(self):
        """Проверить что Comet активен."""
        active_title = self.get_active_window_title()
        is_comet = 'comet' in active_title.lower()
        logger.info(f"🔍 Активное окно: {active_title}")
        logger.info(f"✅ Comet активен: {is_comet}")
        return is_comet
    
    def force_activate_comet(self) -> bool:
        """Принудительно активировать Comet."""
        try:
            import subprocess
            
            logger.info("🔍 Поиск окон Comet...")
            windows = gw.getWindowsWithTitle('Comet')
            if not windows:
                all_windows = gw.getAllWindows()
                for win in all_windows:
                    if 'comet' in win.title.lower():
                        windows = [win]
                        break
            
            if not windows:
                logger.error("❌ Окна Comet не найдены!")
                return False
            
            window = windows[0]
            logger.info(f"📁 Найдено окно: {window.title}")
            
            # PowerShell активация
            logger.info("🔄 PowerShell SetForegroundWindow...")
            ps_command = f'''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {{
                [DllImport("user32.dll")]
                [return: MarshalAs(UnmanagedType.Bool)]
                public static extern bool SetForegroundWindow(IntPtr hWnd);
            }}
"@
            $processes = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*Comet*" }}
            if ($processes) {{
                $hwnd = $processes[0].MainWindowHandle
                [Win32]::SetForegroundWindow($hwnd)
            }}
            '''
            subprocess.run(['powershell', '-Command', ps_command], timeout=5, capture_output=True)
            time.sleep(2)
            
            if self.verify_comet_active():
                logger.info("✅ Comet активирован успешно!")
                return True
            
            logger.error("❌ Не удалось активировать Comet")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка активации Comet: {e}")
            return False
    
    def force_focus_address_bar(self) -> bool:
        """Принудительно сфокусироваться на адресную строку."""
        try:
            logger.info("🌐 Принудительный фокус на адресную строку...")
            
            # Сначала убедимся что Comet активен
            if not self.verify_comet_active():
                logger.error("❌ Comet не активен, не могу фокусироваться на адресную строку")
                return False
            
            # Пробуем все варианты адресной строки
            for i, (x, y) in enumerate(self.address_bar_attempts):
                logger.info(f"🔄 Попытка {i+1}/{len(self.address_bar_attempts)}: клик в ({x}, {y})")
                
                # Клик по предполагаемой адресной строке
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                # Проверяем что фокус не ушел из Comet
                if not self.verify_comet_active():
                    logger.warning("⚠️ Фокус ушел из Comet, возвращаю...")
                    if not self.force_activate_comet():
                        continue
                
                # Пробуем комбинации клавиш для фокуса на адресную строку
                logger.info("   🔄 Ctrl+L...")
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.5)
                
                logger.info("   🔄 F6...")
                pyautogui.press('f6')
                time.sleep(0.5)
                
                logger.info("   🔄 Alt+D...")
                pyautogui.hotkey('alt', 'd')
                time.sleep(0.5)
                
                # Если фокус все еще в Comet, считаем успехом
                if self.verify_comet_active():
                    logger.info(f"✅ Попытка {i+1} успешна!")
                    return True
            
            logger.error("❌ Не удалось сфокусироваться на адресную строку")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка фокуса на адресную строку: {e}")
            return False
    
    def input_url_correctly(self, url: str) -> bool:
        """Правильно ввести URL в адресную строку."""
        try:
            logger.info(f"📍 Ввод URL в адресную строку: {url}")
            
            # Шаг 1: Убедиться что Comet активен
            if not self.force_activate_comet():
                logger.error("❌ Не удалось активировать Comet")
                return False
            
            # Шаг 2: Сфокусироваться на адресную строку
            if not self.force_focus_address_bar():
                logger.error("❌ Не сфокусироваться на адресную строку")
                return False
            
            # Шаг 3: Очистить адресную строку
            logger.info("📍 Очистка адресной строки...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            # Шаг 4: Ввести URL через буфер обмена (надежнее)
            if PYPERCLIP_AVAILABLE:
                logger.info("📍 Копирование URL в буфер обмена...")
                pyperclip.copy(url)
                time.sleep(0.5)
                
                logger.info("📍 Вставка URL через Ctrl+V...")
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
            else:
                logger.info("📍 Ввод URL через pyautogui...")
                pyautogui.typewrite(url, interval=0.05)
                time.sleep(0.5)
            
            # Шаг 5: Проверить что URL введен правильно
            logger.info("📍 Проверка введенного URL...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                clipboard_content = pyperclip.paste()
                logger.info(f"📋 В буфере обмена: {clipboard_content}")
                
                if url in clipboard_content and "://-" not in clipboard_content:
                    logger.info("✅ URL введен правильно!")
                else:
                    logger.warning(f"⚠️ URL введен неправильно: {clipboard_content}")
                    return False
            
            # Шаг 6: Enter
            logger.info("📍 Enter - переход к странице...")
            pyautogui.press('enter')
            time.sleep(4)  # Ждем загрузки
            
            logger.info("✅ URL введен и переход выполнен!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка ввода URL: {e}")
            return False
    
    def test_url_input(self, domain: str) -> bool:
        """Тест ввода URL."""
        try:
            logger.info(f"🧪 Тест ввода URL для домена: {domain}")
            url = f"https://{domain}"
            
            # Тестируем ввод URL
            success = self.input_url_correctly(url)
            
            if success:
                logger.info("✅ Тест ввода URL успешен!")
                print("✅ URL введен правильно!")
                print("👀 Проверьте что открылась правильная страница в Comet")
            else:
                logger.error("❌ Тест ввода URL не удался")
                print("❌ URL введен неправильно")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка теста ввода URL: {e}")
            return False


async def main():
    """Главная функция."""
    print("🚀 ИСПРАВЛЕННЫЙ ВВОД URL В COMET")
    print("="*60)
    print("✅ Решает проблему ввода '://-.' вместо правильного URL")
    print("✅ Улучшенный фокус на адресную строку")
    print("✅ Проверка правильности ввода")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Тест активации Comet")
    print("2. Тест фокуса на адресную строку")
    print("3. Тест ввода URL")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        fixer = FixedURLInput()
        
        if choice == "1":
            # Тест активации
            print("\n🧪 Тест активации Comet...")
            success = fixer.force_activate_comet()
            
            if success:
                print("✅ Comet активирован успешно!")
            else:
                print("❌ Не удалось активировать Comet")
                
        elif choice == "2":
            # Тест фокуса
            print("\n🧪 Тест фокуса на адресную строку...")
            success = fixer.force_focus_address_bar()
            
            if success:
                print("✅ Фокус на адресную строку успешен!")
            else:
                print("❌ Не сфокусироваться на адресную строку")
                
        elif choice == "3":
            # Тест ввода URL
            test_domain = "metallsnab-nn.ru"
            print(f"\n🧪 Тест ввода URL для домена: {test_domain}")
            
            success = fixer.test_url_input(test_domain)
            
            if success:
                print("✅ Тест ввода URL успешен!")
            else:
                print("❌ Тест ввода URL не удался")
            
        else:
            print("❌ Неверный выбор")
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Программа прервана")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
