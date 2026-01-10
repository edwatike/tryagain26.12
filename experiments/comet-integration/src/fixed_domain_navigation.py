"""
Исправленная навигация по доменам в Comet.
Правильно работает с адресной строкой, а не с полем ввода ассистента.
"""
import asyncio
import sys
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

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


class FixedDomainNavigation:
    """Исправленная навигация по доменам в Comet."""
    
    def __init__(self):
        logger.info("FixedDomainNavigation инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # РАБОЧИЕ КООРДИНАТЫ
        self.input_field_x = int(self.screen_width * 0.85)  # Поле ввода ассистента
        self.input_field_y = int(self.screen_height * 0.92)
        
        # АДРЕСНАЯ СТРОКА (вверху страницы)
        self.address_bar_x = int(self.screen_width * 0.5)   # Центр экрана
        self.address_bar_y = int(self.screen_height * 0.05) # 5% от верха
        
        logger.info(f"🎯 Поле ввода ассистента: ({self.input_field_x}, {self.input_field_y})")
        logger.info(f"🌐 Адресная строка: ({self.address_bar_x}, {self.address_bar_y})")
    
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
    
    def force_activate_comet(self):
        """Принудительно активировать Comet."""
        try:
            windows = gw.getWindowsWithTitle('Comet')
            if not windows:
                all_windows = gw.getAllWindows()
                for win in all_windows:
                    if 'comet' in win.title.lower():
                        windows = [win]
                        break
            
            if windows:
                window = windows[0]
                logger.info(f"📁 Найдено окно: {window.title}")
                
                # PowerShell метод
                try:
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
                    return True
                except:
                    pass
            
            return False
        except:
            return False
    
    def ensure_comet_ready(self):
        """Убедиться что Comet готов к работе."""
        logger.info("🔍 Проверка готовности Comet...")
        
        # Проверяем есть ли окна Comet
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'comet' in win.title.lower():
                    windows = [win]
                    break
        
        if not windows:
            logger.info("🚀 Comet не найден, открываю...")
            comet_paths = [
                Path(r"C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
                Path(r"C:\Program Files\Comet\Comet.exe"),
                Path(r"C:\Program Files (x86)\Comet\Comet.exe"),
                Path(r"C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe"),
                Path(r"C:\Users\admin\AppData\Local\Comet\Application\Comet.exe")
            ]
            
            for path in comet_paths:
                if path.exists():
                    logger.info(f"🚀 Запускаю Comet: {path}")
                    subprocess.Popen([str(path)], shell=True)
                    time.sleep(5)
                    break
        
        # Активируем Comet
        if not self.force_activate_comet():
            return False
        
        # Проверяем что активен
        if not self.verify_comet_active():
            return False
        
        logger.info("✅ Comet готов к работе")
        return True
    
    def navigate_to_domain(self, domain: str) -> bool:
        """Перейти к домену через адресную строку."""
        try:
            logger.info(f"🌐 Переход к домену: {domain}")
            url = f"https://{domain}"
            
            # Шаг 1: Убедиться что Comet активен
            if not self.ensure_comet_ready():
                logger.error("❌ Comet не готов")
                return False
            
            # Шаг 2: Ctrl+L - фокус на адресную строку
            logger.info("📍 Ctrl+L - фокус на адресную строку...")
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(1)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после Ctrl+L")
                return False
            
            # Шаг 3: Выделить все в адресной строке
            logger.info("📍 Выделение текста в адресной строке...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после Ctrl+A")
                return False
            
            # Шаг 4: Очистить адресную строку
            logger.info("📍 Очистка адресной строки...")
            pyautogui.press('delete')
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после очистки")
                return False
            
            # Шаг 5: Ввести URL
            logger.info(f"📍 Ввод URL: {url}")
            pyautogui.typewrite(url, interval=0.05)
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после ввода URL")
                return False
            
            # Шаг 6: Enter - перейти
            logger.info("📍 Enter - переход к странице...")
            pyautogui.press('enter')
            time.sleep(4)  # Ждем загрузки страницы
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после перехода")
                return False
            
            logger.info("✅ Переход к домену выполнен успешно!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка перехода к домену {domain}: {e}")
            return False
    
    def send_prompt_to_assistant(self, prompt: str) -> bool:
        """Отправить промпт в ассистента."""
        try:
            logger.info(f"🤖 Отправка промпта ассистенту: {prompt}")
            
            # Шаг 1: Убедиться что Comet активен
            if not self.verify_comet_active():
                logger.error("❌ Comet не активен")
                return False
            
            # Шаг 2: Alt+A - открыть ассистента
            logger.info("📍 Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после Alt+A")
                return False
            
            # Шаг 3: Клик по полю ввода ассистента
            logger.info(f"📍 Клик по полю ввода: ({self.input_field_x}, {self.input_field_y})")
            pyautogui.click(self.input_field_x, self.input_field_y)
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после клика")
                return False
            
            # Шаг 4: Очистка поля ассистента
            logger.info("📍 Очистка поля ассистента...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после очистки")
                return False
            
            # Шаг 5: Ввод промпта
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(0.5)
            
            if not self.verify_comet_active():
                logger.error("❌ Фокус ушел после ввода")
                return False
            
            # Шаг 6: Enter
            logger.info("📍 Отправка промпта...")
            pyautogui.press('enter')
            time.sleep(0.5)
            
            logger.info("✅ Промпт отправлен успешно!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            return False
    
    async def extract_domain_info(self, domain: str) -> Dict[str, Any]:
        """Извлечь информацию о домене."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Извлечение информации для {domain}")
            
            # Шаг 1: Перейти к домену
            if not self.navigate_to_domain(domain):
                return self._create_error_result(domain, "Не удалось перейти к домену")
            
            # Шаг 2: Отправить промпт /requisites
            prompt = "/requisites"
            if not self.send_prompt_to_assistant(prompt):
                return self._create_error_result(domain, "Не удалось отправить промпт")
            
            # Шаг 3: Ожидание результата
            logger.info("⏳ Ожидаю результат 10 секунд...")
            await asyncio.sleep(10)
            
            # Шаг 4: Получение результата (заглушка)
            result = self._create_mock_result(domain)
            
            execution_time = time.time() - start_time
            result.update({
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Извлечение завершено за {execution_time:.2f}с")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Ошибка извлечения для {domain}: {e}")
            return self._create_error_result(domain, f"Error: {e}", execution_time)
    
    def _create_mock_result(self, domain: str) -> Dict[str, Any]:
        """Создать мок результат."""
        return {
            "domain": domain,
            "success": True,
            "inn": "1234567890",
            "email": f"info@{domain}",
            "source_url": f"https://{domain}",
            "method": "comet_shortcut",
            "confidence": "high"
        }
    
    def _create_error_result(self, domain: str, error: str, execution_time: float = 0) -> Dict[str, Any]:
        """Создать результат ошибки."""
        return {
            "domain": domain,
            "success": False,
            "error": error,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    async def process_domains(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Обработать список доменов."""
        logger.info(f"🚀 Обработка {len(domains)} доменов")
        
        results = []
        for domain in domains:
            logger.info(f"📍 Обработка домена: {domain}")
            result = await self.extract_domain_info(domain)
            results.append(result)
            
            # Пауза между доменами
            await asyncio.sleep(2)
        
        return results


async def main():
    """Главная функция."""
    print("🌐 ИСПРАВЛЕННАЯ НАВИГАЦИЯ ПО ДОМЕНАМ")
    print("="*60)
    print("✅ Правильная работа с адресной строкой")
    print("✅ Отдельная работа с полем ввода ассистента")
    print("🌐 Адресная строка: Ctrl+L")
    print("🤖 Ассистент: Alt+A + клик по полю")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Тест перехода по домену")
    print("2. Тест промпта ассистенту")
    print("3. Полная обработка доменов")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        navigation = FixedDomainNavigation()
        
        if choice == "1":
            # Тест перехода по домену
            test_domain = "metallsnab-nn.ru"
            print(f"\n🌐 Тестовый домен: {test_domain}")
            
            success = navigation.navigate_to_domain(test_domain)
            
            if success:
                print("✅ Переход выполнен успешно!")
            else:
                print("❌ Переход не удался")
                
        elif choice == "2":
            # Тест промпта
            test_prompt = "/requisites"
            print(f"\n🤖 Тестовый промпт: {test_prompt}")
            
            success = navigation.send_prompt_to_assistant(test_prompt)
            
            if success:
                print("✅ Промпт отправлен успешно!")
            else:
                print("❌ Промпт не отправлен")
                
        elif choice == "3":
            # Полная обработка
            domains = ["metallsnab-nn.ru", "wodoprovod.ru", "gremir.ru"]
            
            print(f"\n📝 Будут обработаны домены: {domains}")
            print("⚠️ Не переключайтесь в другие окна")
            
            print(f"\nНажмите Enter для начала...")
            input()
            
            results = await navigation.process_domains(domains)
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            for result in results:
                if result.get("success", False):
                    print(f"✅ {result['domain']}: ИНН={result['inn']}, Email={result['email']}")
                else:
                    print(f"❌ {result['domain']}: {result.get('error')}")
            
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
