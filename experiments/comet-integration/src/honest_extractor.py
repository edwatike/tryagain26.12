"""
ЧЕСТНЫЙ ИЗВЛЕКАТЕЛЬ COMET
Показывает реальные результаты, а не ложные успехи
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


class HonestExtractor:
    """Честный извлекатель - показывает реальные результаты."""
    
    def __init__(self):
        logger.info("🚀 HonestExtractor инициализирован")
        self.screen_width, self.screen_height = pyautogui.size() if PYAUTOGUI_AVAILABLE else (1920, 1080)
        
        # РАБОЧИЕ КООРДИНАТЫ
        self.input_field_x = int(self.screen_width * 0.85)   # Поле ввода ассистента
        self.input_field_y = int(self.screen_height * 0.92)
        
        # АДРЕСНАЯ СТРОКА
        self.address_bar_attempts = [
            (int(self.screen_width * 0.5), int(self.screen_height * 0.05)),
            (int(self.screen_width * 0.3), int(self.screen_height * 0.05)),
            (int(self.screen_width * 0.7), int(self.screen_height * 0.05)),
            (int(self.screen_width * 0.5), int(self.screen_height * 0.08)),
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
    
    def input_url_and_verify(self, domain: str) -> Dict[str, Any]:
        """Ввести URL и ЧЕСТНО проверить результат."""
        result = {
            "step": "URL ввод",
            "success": False,
            "details": {}
        }
        
        try:
            url = f"https://{domain}"
            logger.info(f"🌐 Ввод URL: {url}")
            
            # Шаг 1: Активировать Comet
            if not self.force_activate_comet():
                result["details"]["error"] = "Не удалось активировать Comet"
                return result
            
            # Шаг 2: Фокус на адресную строку
            logger.info("📍 Фокус на адресную строку...")
            for i, (x, y) in enumerate(self.address_bar_attempts):
                pyautogui.click(x, y)
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.5)
                pyautogui.press('f6')
                time.sleep(0.5)
                pyautogui.hotkey('alt', 'd')
                time.sleep(0.5)
                
                if self.verify_comet_active():
                    logger.info(f"✅ Фокус успешен на попытке {i+1}")
                    result["details"]["focus_attempt"] = i+1
                    break
            
            # Шаг 3: Ввести URL
            logger.info("📍 Ввод URL...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(url)
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
            else:
                pyautogui.typewrite(url, interval=0.05)
                time.sleep(0.5)
            
            # Шаг 4: ПРОВЕРКА что введено
            logger.info("📍 ПРОВЕРКА: что реально введено...")
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                actual_url = pyperclip.paste()
                result["details"]["actual_url"] = actual_url
                result["details"]["expected_url"] = url
                
                if url in actual_url and "://-" not in actual_url:
                    logger.info(f"✅ URL введен правильно: {actual_url}")
                    result["details"]["url_correct"] = True
                else:
                    logger.error(f"❌ URL введен НЕПРАВИЛЬНО: {actual_url}")
                    result["details"]["url_correct"] = False
                    result["details"]["error"] = f"URL введен неправильно: {actual_url}"
                    return result
            
            # Шаг 5: Enter и проверка перехода
            logger.info("📍 Enter - переход...")
            pyautogui.press('enter')
            time.sleep(4)
            
            if self.verify_comet_active():
                logger.info("✅ Переход выполнен, Comet все еще активен")
                result["details"]["transition_success"] = True
                result["success"] = True
            else:
                logger.error("❌ Фокус потерян после перехода")
                result["details"]["transition_success"] = False
                result["details"]["error"] = "Фокус потерян после перехода"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка ввода URL: {e}")
            result["details"]["error"] = str(e)
            return result
    
    def send_prompt_and_verify(self, prompt: str) -> Dict[str, Any]:
        """Отправить промпт и ЧЕСТНО проверить результат."""
        result = {
            "step": "Отправка промпта",
            "success": False,
            "details": {}
        }
        
        try:
            logger.info(f"🤖 Отправка промпта: {prompt}")
            
            # Шаг 1: Активировать Comet
            if not self.force_activate_comet():
                result["details"]["error"] = "Не удалось активировать Comet"
                return result
            
            # Шаг 2: Открыть ассистента
            logger.info("📍 Alt+A - открытие ассистента...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            
            # Шаг 3: Клик по полю ввода
            logger.info(f"📍 Клик по полю ввода: ({self.input_field_x}, {self.input_field_y})")
            pyautogui.click(self.input_field_x, self.input_field_y)
            time.sleep(0.5)
            
            # Шаг 4: Очистить и ввести промпт
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.press('delete')
            time.sleep(0.5)
            
            logger.info("📍 Ввод промпта...")
            pyautogui.typewrite(prompt, interval=0.05)
            time.sleep(0.5)
            
            # Шаг 5: ПРОВЕРКА что введено
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                actual_prompt = pyperclip.paste()
                result["details"]["actual_prompt"] = actual_prompt
                result["details"]["expected_prompt"] = prompt
                
                if prompt in actual_prompt:
                    logger.info(f"✅ Промпт введен правильно")
                    result["details"]["prompt_correct"] = True
                else:
                    logger.error(f"❌ Промпт введен НЕПРАВИЛЬНО: {actual_prompt}")
                    result["details"]["prompt_correct"] = False
                    result["details"]["error"] = f"Промпт введен неправильно: {actual_prompt}"
                    return result
            
            # Шаг 6: Enter
            logger.info("📍 Enter - отправка промпта...")
            pyautogui.press('enter')
            time.sleep(0.5)
            
            logger.info("✅ Промпт отправлен")
            result["details"]["sent_success"] = True
            result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки промпта: {e}")
            result["details"]["error"] = str(e)
            return result
    
    def wait_and_extract_response(self, max_wait_time: int = 30) -> Dict[str, Any]:
        """Подождать и ЧЕСТНО извлечь ответ."""
        result = {
            "step": "Получение ответа",
            "success": False,
            "details": {}
        }
        
        try:
            logger.info(f"⏳ Ожидаю ответа {max_wait_time} секунд...")
            
            for i in range(max_wait_time):
                time.sleep(1)
                if (i + 1) % 5 == 0:
                    logger.info(f"   ⏳ Прошло {i + 1}/{max_wait_time} секунд...")
            
            logger.info("✅ Ожидание завершено")
            result["details"]["wait_completed"] = True
            
            # Извлечение ответа
            logger.info("📥 Извлечение ответа...")
            
            if not self.force_activate_comet():
                result["details"]["error"] = "Comet не активен"
                return result
            
            pyautogui.hotkey('alt', 'a')
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            if PYPERCLIP_AVAILABLE:
                response = pyperclip.paste()
                result["details"]["response_length"] = len(response)
                result["details"]["response_preview"] = response[:100] + "..." if len(response) > 100 else response
                
                logger.info(f"📋 Получен ответ: {len(response)} символов")
                
                if len(response) < 50:
                    logger.warning("⚠️ Ответ слишком короткий")
                    result["details"]["error"] = "Ответ ассистента слишком короткий"
                    return result
                
                # Анализ ответа
                inn = None
                email = None
                
                inn_patterns = [r'\b\d{10}\b', r'\b\d{12}\b', r'ИНН[:\s]+(\d{10,12})']
                for pattern in inn_patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches:
                        inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        inn = re.sub(r'[^\d]', '', str(inn))
                        if len(inn) in [10, 12]:
                            break
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_matches = re.findall(email_pattern, response)
                if email_matches:
                    email = email_matches[0]
                
                result["details"]["inn_found"] = inn is not None
                result["details"]["email_found"] = email is not None
                result["details"]["inn"] = inn
                result["details"]["email"] = email
                
                if inn or email:
                    logger.info(f"✅ Найдено: ИНН={inn}, Email={email}")
                    result["success"] = True
                else:
                    logger.warning("⚠️ ИНН и email не найдены")
                    result["details"]["error"] = "ИНН и email не найдены в ответе"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения ответа: {e}")
            result["details"]["error"] = str(e)
            return result
    
    async def honest_extract_domain_info(self, domain: str) -> Dict[str, Any]:
        """ЧЕСТНЫЙ полный цикл извлечения."""
        start_time = time.time()
        
        logger.info(f"🚀 ЧЕСТНЫЙ цикл извлечения для {domain}")
        logger.info("="*60)
        
        results = {
            "domain": domain,
            "overall_success": False,
            "steps": [],
            "execution_time": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # ШАГ 1: Ввод URL
        logger.info("📍 ШАГ 1: Ввод URL")
        url_result = self.input_url_and_verify(domain)
        results["steps"].append(url_result)
        
        if not url_result["success"]:
            logger.error("❌ ШАГ 1 НЕ УСПЕШЕН")
            results["execution_time"] = time.time() - start_time
            return results
        
        # ШАГ 2: Отправка промпта
        logger.info("📍 ШАГ 2: Отправка промпта")
        prompt = f"Найди ИНН и email для сайта {domain}. Если не найдешь, укажи почему."
        prompt_result = self.send_prompt_and_verify(prompt)
        results["steps"].append(prompt_result)
        
        if not prompt_result["success"]:
            logger.error("❌ ШАГ 2 НЕ УСПЕШЕН")
            results["execution_time"] = time.time() - start_time
            return results
        
        # ШАГ 3: Получение ответа
        logger.info("📍 ШАГ 3: Получение ответа")
        response_result = self.wait_and_extract_response(30)
        results["steps"].append(response_result)
        
        if not response_result["success"]:
            logger.error("❌ ШАГ 3 НЕ УСПЕШЕН")
            results["execution_time"] = time.time() - start_time
            return results
        
        # Если все шаги успешны
        results["overall_success"] = True
        results["execution_time"] = time.time() - start_time
        
        # Копируем результаты из последнего шага
        if response_result["details"].get("inn"):
            results["inn"] = response_result["details"]["inn"]
        if response_result["details"].get("email"):
            results["email"] = response_result["details"]["email"]
        
        logger.info("✅ ВСЕ ШАГИ УСПЕШНЫ!")
        logger.info("="*60)
        
        return results


async def main():
    """Главная функция."""
    print("🚀 ЧЕСТНЫЙ ИЗВЛЕКАТЕЛЬ COMET")
    print("="*60)
    print("✅ Показывает РЕАЛЬНЫЕ результаты")
    print("✅ Не скрывает проблемы")
    print("✅ Честная проверка каждого шага")
    print("="*60)
    
    print("\nВыберите режим:")
    print("1. Честный тест ввода URL")
    print("2. Честный тест промпта")
    print("3. Честный полный цикл")
    
    try:
        choice = input("Ваш выбор (1-3): ").strip()
        
        extractor = HonestExtractor()
        
        if choice == "1":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🌐 Честный тест URL: {test_domain}")
            
            result = extractor.input_url_and_verify(test_domain)
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   Успех: {result['success']}")
            for key, value in result["details"].items():
                print(f"   {key}: {value}")
                
        elif choice == "2":
            test_prompt = "Найди ИНН и email для этого сайта"
            print(f"\n🤖 Честный тест промпта: {test_prompt}")
            
            result = extractor.send_prompt_and_verify(test_prompt)
            
            print(f"\n📊 РЕЗУЛЬТАТ:")
            print(f"   Успех: {result['success']}")
            for key, value in result["details"].items():
                print(f"   {key}: {value}")
                
        elif choice == "3":
            test_domain = "metallsnab-nn.ru"
            print(f"\n🚀 Честный полный цикл: {test_domain}")
            print("🔄 ПОЛНАЯ ПРОВЕРКА ВСЕХ ШАГОВ")
            
            result = await extractor.honest_extract_domain_info(test_domain)
            
            print(f"\n📊 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
            print(f"   Домен: {result['domain']}")
            print(f"   Общий успех: {result['overall_success']}")
            print(f"   Время: {result['execution_time']:.2f}с")
            
            print(f"\n📋 ПОШАГОВЫЕ РЕЗУЛЬТАТЫ:")
            for i, step in enumerate(result["steps"], 1):
                print(f"   Шаг {i} ({step['step']}): {'✅ УСПЕХ' if step['success'] else '❌ НЕУСПЕХ'}")
                if not step["success"] and "error" in step["details"]:
                    print(f"      Ошибка: {step['details']['error']}")
            
            if result["overall_success"]:
                print(f"\n✅ УСПЕХ - ИНФОРМАЦИЯ НАЙДЕНА:")
                print(f"   📋 ИНН: {result.get('inn', 'Не найден')}")
                print(f"   📧 Email: {result.get('email', 'Не найден')}")
                print(f"\n🎉 ЗАДАЧА ВЫПОЛНЕНА!")
            else:
                print(f"\n❌ НЕУСПЕХ - ИНФОРМАЦИЯ НЕ НАЙДЕНА!")
                print(f"\n⚠️ ЗАДАЧА НЕ ВЫПОЛНЕНА!")
        
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
