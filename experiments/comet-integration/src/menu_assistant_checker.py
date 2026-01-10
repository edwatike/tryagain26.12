"""
ПРОВЕРКА АССИСТЕНТА ЧЕРЕЗ МЕНЮ COMET
Ищет ассистента через меню и настройки
"""
import asyncio
import sys
import time
import subprocess
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


class MenuAssistantChecker:
    """Проверка ассистента через меню."""
    
    def __init__(self):
        logger.info("🚀 MenuAssistantChecker инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # Пути к Comet
        self.comet_paths = [
            Path(r'C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe'),
            Path(r'C:\Program Files\Comet\Comet.exe'),
            Path(r'C:\Program Files (x86)\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe'),
            Path(r'C:\Users\admin\AppData\Local\Comet\Application\Comet.exe'),
        ]
        
        logger.info(f"🌐 Экран: {self.screen_width}x{self.screen_height}")
    
    def find_comet_executable(self) -> Path:
        """Найти исполняемый файл Comet."""
        for path in self.comet_paths:
            if path.exists():
                logger.info(f"✅ Найден Comet: {path}")
                return path
        logger.error("❌ Comet не найден!")
        return None
    
    def launch_comet_with_url(self, url: str) -> bool:
        """Запустить Comet с указанным URL."""
        try:
            logger.info(f"🚀 Запуск Comet с URL: {url}")
            
            comet_exe = self.find_comet_executable()
            if not comet_exe:
                return False
            
            # Закрыть существующие окна
            try:
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Comet.exe'], 
                                      capture_output=True, text=True, timeout=5)
                if 'Comet.exe' in result.stdout:
                    subprocess.run(['taskkill', '/F', '/IM', 'Comet.exe'], 
                                  capture_output=True, timeout=5)
                    time.sleep(2)
            except:
                pass
            
            # Запуск Comet с URL
            logger.info(f"📍 Запуск: {comet_exe} {url}")
            subprocess.Popen([str(comet_exe), url], shell=True)
            
            # Ждем загрузки
            logger.info("⏳ Ожидаю загрузки Comet...")
            time.sleep(8)
            
            # Проверяем что Comet открыт
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    logger.info(f"✅ Comet открыт: {windows[0].title}")
                    return True
            
            logger.error("❌ Comet не найден после запуска")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска Comet: {e}")
            return False
    
    def activate_comet_window(self) -> bool:
        """Активировать окно Comet."""
        try:
            if PYGETWINDOW_AVAILABLE:
                windows = gw.getWindowsWithTitle('Comet')
                if windows:
                    windows[0].activate()
                    time.sleep(1)
                    return True
            return False
        except:
            return False
    
    def check_assistant_in_menu(self) -> bool:
        """Проверить наличие ассистента в меню."""
        logger.info("🔍 Проверяю наличие ассистента в меню...")
        
        try:
            # Активируем окно
            self.activate_comet_window()
            time.sleep(1)
            
            # Пробуем открыть меню
            logger.info("📍 Пробую Alt (меню)...")
            pyautogui.press('alt')
            time.sleep(2)
            
            # Ищем пункты меню связанные с ассистентом
            menu_keywords = ['assistant', 'ai', 'chat', 'help', 'assistant', 'помощник', 'ассистент']
            
            # Пробуем Tab для навигации по меню
            for i in range(10):
                pyautogui.press('tab')
                time.sleep(0.5)
                
                # Проверяем что в фокусе
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                if PYPERCLIP_AVAILABLE:
                    menu_text = pyperclip.paste().lower()
                    for keyword in menu_keywords:
                        if keyword in menu_text:
                            logger.info(f"✅ Найден пункт меню: {menu_text}")
                            pyautogui.press('enter')
                            time.sleep(2)
                            return True
            
            # Пробуем Escape чтобы закрыть меню
            pyautogui.press('escape')
            time.sleep(1)
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки меню: {e}")
            return False
    
    def check_assistant_in_toolbar(self) -> bool:
        """Проверить наличие ассистента на панели инструментов."""
        logger.info("🔍 Проверяю наличие ассистента на панели инструментов...")
        
        try:
            # Активируем окно
            self.activate_comet_window()
            time.sleep(1)
            
            # Ищем иконки на панели инструментов
            toolbar_areas = [
                (int(self.screen_width * 0.1), int(self.screen_height * 0.05)),  # Левый верхний
                (int(self.screen_width * 0.5), int(self.screen_height * 0.05)),  # Центр верхний
                (int(self.screen_width * 0.9), int(self.screen_height * 0.05)),  # Правый верхний
                (int(self.screen_width * 0.1), int(self.screen_height * 0.95)),  # Левый нижний
                (int(self.screen_width * 0.9), int(self.screen_height * 0.95)),  # Правый нижний
            ]
            
            for i, (x, y) in enumerate(toolbar_areas):
                logger.info(f"🔄 Проверяю область панели {i+1}/5: ({x}, {y})")
                
                # Клик по области
                pyautogui.click(x, y)
                time.sleep(1)
                
                # Пробуем открыть ассистента
                pyautogui.hotkey('alt', 'a')
                time.sleep(2)
                
                # Проверяем что ассистент открыт
                if self.check_assistant_open():
                    logger.info(f"✅ Ассистент найден на панели {i+1}!")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки панели: {e}")
            return False
    
    def check_assistant_open(self) -> bool:
        """Проверить что ассистент открыт."""
        try:
            # Пробуем ввести тестовый символ
            test_x, test_y = int(self.screen_width * 0.85), int(self.screen_height * 0.92)
            pyautogui.click(test_x, test_y)
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            pyautogui.typewrite('TEST')
            time.sleep(0.5)
            
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                clipboard_content = pyperclip.paste()
                if 'TEST' in clipboard_content:
                    # Очищаем тест
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.press('delete')
                    time.sleep(0.5)
                    return True
            
            return False
        except:
            return False
    
    def check_login_required(self) -> bool:
        """Проверить нужно ли войти в аккаунт."""
        logger.info("🔍 Проверяю нужно ли войти в аккаунт...")
        
        try:
            # Активируем окно
            self.activate_comet_window()
            time.sleep(1)
            
            # Ищем элементы входа
            login_keywords = ['login', 'sign', 'войти', 'вход', 'log in']
            
            # Проверяем наличие кнопок входа
            login_areas = [
                (int(self.screen_width * 0.5), int(self.screen_height * 0.3)),
                (int(self.screen_width * 0.5), int(self.screen_height * 0.5)),
                (int(self.screen_width * 0.5), int(self.screen_height * 0.7)),
            ]
            
            for x, y in login_areas:
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                
                if PYPERCLIP_AVAILABLE:
                    text = pyperclip.paste().lower()
                    for keyword in login_keywords:
                        if keyword in text:
                            logger.info(f"✅ Найден элемент входа: {text}")
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки входа: {e}")
            return False
    
    def comprehensive_assistant_check(self, domain: str) -> Dict[str, Any]:
        """Комплексная проверка ассистента."""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Комплексная проверка ассистента для {domain}")
            logger.info("="*60)
            
            url = f"https://{domain}"
            
            # Шаг 1: Запуск Comet
            logger.info("📍 ШАГ 1: Запуск Comet")
            if not self.launch_comet_with_url(url):
                return {
                    "domain": domain,
                    "success": False,
                    "error": "Не удалось запустить Comet",
                    "execution_time": time.time() - start_time,
                    "assistant_available": False,
                    "login_required": False
                }
            
            # Шаг 2: Проверка входа
            logger.info("📍 ШАГ 2: Проверка входа в аккаунт")
            login_needed = self.check_login_required()
            
            # Шаг 3: Проверка ассистента в меню
            logger.info("📍 ШАГ 3: Проверка ассистента в меню")
            menu_found = self.check_assistant_in_menu()
            
            if menu_found:
                return {
                    "domain": domain,
                    "success": True,
                    "assistant_method": "menu",
                    "login_required": login_needed,
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 4: Проверка ассистента на панели
            logger.info("📍 ШАГ 4: Проверка ассистента на панели")
            toolbar_found = self.check_assistant_in_toolbar()
            
            if toolbar_found:
                return {
                    "domain": domain,
                    "success": True,
                    "assistant_method": "toolbar",
                    "login_required": login_needed,
                    "execution_time": time.time() - start_time
                }
            
            # Шаг 5: Стандартные методы
            logger.info("📍 ШАГ 5: Стандартные методы")
            standard_methods = [
                ("Alt+A", lambda: pyautogui.hotkey('alt', 'a')),
                ("Ctrl+Shift+A", lambda: pyautogui.hotkey('ctrl', 'shift', 'a')),
                ("F1", lambda: pyautogui.press('f1')),
            ]
            
            for method_name, method_func in standard_methods:
                logger.info(f"🔄 Пробую {method_name}...")
                method_func()
                time.sleep(3)
                
                if self.check_assistant_open():
                    return {
                        "domain": domain,
                        "success": True,
                        "assistant_method": method_name,
                        "login_required": login_needed,
                        "execution_time": time.time() - start_time
                    }
            
            # Ничего не найдено
            return {
                "domain": domain,
                "success": False,
                "error": "Ассистент не найден",
                "assistant_available": False,
                "login_required": login_needed,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Критическая ошибка проверки: {e}")
            return {
                "domain": domain,
                "success": False,
                "error": f"Критическая ошибка: {e}",
                "execution_time": execution_time
            }


async def main():
    """Главная функция."""
    print("🚀 ПРОВЕРКА АССИСТЕНТА ЧЕРЕЗ МЕНЮ COMET")
    print("="*60)
    print("✅ Проверяет наличие ассистента в меню")
    print("✅ Проверяет наличие ассистента на панели")
    print("✅ Проверяет нужно ли войти в аккаунт")
    print("✅ Комплексная проверка всех методов")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Комплексная проверка ассистента")
    print("2. Только проверка входа")
    print("3. Только проверка меню")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        checker = MenuAssistantChecker()
        
        if choice == "1":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🔍 Комплексная проверка ассистента для {test_domain}")
            print("🔄 Будет выполнено:")
            print("   1. Запуск Comet с URL")
            print("   2. Проверка входа в аккаунт")
            print("   3. Поиск ассистента в меню")
            print("   4. Поиск ассистента на панели")
            print("   5. Стандартные методы")
            
            result = checker.comprehensive_assistant_check(test_domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ ПРОВЕРКИ:")
            print(f"   Домен: {result['domain']}")
            print(f"   Успех: {result['success']}")
            print(f"   Время: {result.get('execution_time', 0):.2f}с")
            
            if result.get("success"):
                method = result.get("assistant_method", "неизвестен")
                print(f"   ✅ Ассистент найден через: {method}")
                
                if result.get("login_required"):
                    print(f"   ⚠️ Требуется вход в аккаунт")
                else:
                    print(f"   ✅ Вход не требуется")
                    
                print(f"\n🎉 АССИСТЕНТ ДОСТУПЕН!")
            else:
                error = result.get("error", "Неизвестная ошибка")
                print(f"   ❌ Ошибка: {error}")
                
                if result.get("login_required"):
                    print(f"   ⚠️ Требуется вход в аккаунт")
                else:
                    print(f"   ✅ Вход не требуется")
                
                if not result.get("assistant_available", True):
                    print(f"   ❌ Ассистент недоступен в этой версии Comet")
                    
                print(f"\n⚠️ АССИСТЕНТ НЕ НАЙДЕН!")
                
        elif choice == "2":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🔍 Проверка входа для {test_domain}")
            
            if not checker.launch_comet_with_url(f"https://{test_domain}"):
                print("❌ Не удалось запустить Comet")
                return
            
            login_needed = checker.check_login_required()
            
            if login_needed:
                print("✅ Требуется вход в аккаунт")
            else:
                print("✅ Вход не требуется")
                
        elif choice == "3":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🔍 Проверка меню для {test_domain}")
            
            if not checker.launch_comet_with_url(f"https://{test_domain}"):
                print("❌ Не удалось запустить Comet")
                return
            
            menu_found = checker.check_assistant_in_menu()
            
            if menu_found:
                print("✅ Ассистент найден в меню")
            else:
                print("❌ Ассистент не найден в меню")
        
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
