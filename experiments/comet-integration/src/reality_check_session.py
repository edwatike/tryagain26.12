"""
Сессия с проверкой реальности - действительно ли Comet открыт.
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


class RealityCheckSession:
    """Сессия с проверкой реальности Comet."""
    
    def __init__(self):
        logger.info("RealityCheck сессия инициализирована")
    
    def is_comet_really_open(self) -> bool:
        """
        Проверить действительно ли Comet браузер открыт.
        
        Returns:
            bool: True если Comet реально открыт и работает
        """
        logger.info("🔍 ПРОВЕРКА РЕАЛЬНОСТИ: Comet открыт?")
        
        # Способ 1: Проверка окон
        if PYGETWINDOW_AVAILABLE:
            try:
                windows = gw.getWindowsWithTitle('Comet')
                logger.info(f"📊 Найдено окон 'Comet': {len(windows)}")
                
                if windows:
                    for i, window in enumerate(windows):
                        logger.info(f"   Окно {i+1}: '{window.title}' (размер: {window.size})")
                        
                        # Проверяем что окно реально видимо (не свернуто)
                        if window.size[0] > 100 and window.size[1] > 100:
                            logger.info(f"   ✅ Окно {i+1} имеет реальный размер")
                            return True
                        else:
                            logger.warning(f"   ⚠️ Окно {i+1} свернуто или имеет нулевой размер")
                else:
                    logger.warning("❌ Окна 'Comet' не найдены")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Ошибка проверки окон: {e}")
        
        # Способ 2: Проверка процессов (дополнительная проверка)
        try:
            import psutil
            comet_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'comet' in proc.info()['name'].lower():
                        comet_processes.append(proc.info())
                        logger.info(f"📊 Процесс Comet: PID {proc.pid}")
                except:
                    pass
            
            if comet_processes:
                logger.info(f"✅ Найдено {len(comet_processes)} процессов Comet")
                return True
            else:
                logger.warning("❌ Процессы Comet не найдены")
                return False
                
        except ImportError:
            logger.warning("⚠️ psutil недоступен, пропускаю проверку процессов")
        except Exception as e:
            logger.error(f"❌ Ошибка проверки процессов: {e}")
        
        # Способ 3: Визуальная проверка через скриншот
        try:
            logger.info("📸 Делаю скриншот для визуальной проверки...")
            screenshot = pyautogui.screenshot()
            
            # Ищем Comet в скриншоте (упрощенная проверка)
            # В реальности здесь можно использовать OCR для поиска логотипа Comet
            logger.info(f"📸 Скриншот сделан: {screenshot.size}")
            logger.info("⚠️ OCR проверка не реализована, предполагаем что Comet не виден")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка скриншота: {e}")
        
        return False
    
    async def open_comet_manually(self) -> bool:
        """
        Открыть Comet - сначала автоматически, потом вручную если нужно.
        
        Returns:
            bool: True если Comet открыт и работает
        """
        logger.info("🚀 ПОПЫТКА АВТОМАТИЧЕСКОГО ОТКРЫТИЯ COMET")
        
        # Способ 1: Пытаемся найти и запустить Comet
        comet_paths = [
            Path(r"C:\Users\admin\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
            Path(r"C:\Program Files\Comet\Comet.exe"),
            Path(r"C:\Program Files (x86)\Comet\Comet.exe"),
            Path(r"C:\Users\admin\AppData\Local\Programs\Comet\Comet.exe"),
            Path(r"C:\Users\admin\AppData\Local\Comet\Application\Comet.exe")
        ]
        
        for comet_path in comet_paths:
            if comet_path.exists():
                logger.info(f"📁 Найден Comet по пути: {comet_path}")
                try:
                    logger.info("🚀 Запускаю Comet...")
                    subprocess.Popen([str(comet_path)], shell=True)
                    
                    # Ждем запуска
                    logger.info("⏳ Жду запуска Comet (5 секунд)...")
                    await asyncio.sleep(5)
                    
                    # Проверяем что Comet открылся
                    if self.is_comet_really_open():
                        logger.info("✅ Comet успешно открыт автоматически!")
                        print("✅ Comet успешно открыт автоматически!")
                        return True
                    else:
                        logger.warning("⚠️ Comet запущен, но окно не найдено")
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка запуска Comet: {e}")
                    continue
            else:
                logger.debug(f"📁 Comet не найден по пути: {comet_path}")
        
        # Способ 2: Если автоматическое открытие не сработало - вручную
        logger.info("🔄 Автоматическое открытие не удалось, пробую вручную")
        print("🖥️ РУЧНОЕ ОТКРЫТИЕ COMET")
        print("="*50)
        print("📋 Инструкция:")
        print("1. Найдите Comet браузер")
        print("2. Откройте его")
        print("3. Убедитесь что он на экране")
        print("4. Активируйте окно (кликните на него)")
        print("="*50)
        
        print(f"\n⚠️  ВАЖНО:")
        print("   ✅ Comet должен быть видим на экране")
        print("   ✅ Окно должно быть активно")
        print("   ✅ Не свернуто")
        
        print(f"\n🔍 Пути к Comet (обычно):")
        for path in comet_paths:
            print(f"   {path}")
        
        print(f"\nНажмите Enter когда Comet открыт и активен...")
        input()
        
        # Проверяем что Comet реально открыт
        if self.is_comet_really_open():
            print("✅ Comet действительно открыт и работает!")
            return True
        else:
            print("❌ Comet не найден или не работает!")
            print("💡 Убедитесь что:")
            print("   - Comet установлен")
            print("   - Comet запущен")
            print("   - Окно Comet активно")
            return False
    
    async def test_input_with_real_check(self) -> bool:
        """
        Тест ввода с проверкой реальности.
        
        Returns:
            bool: True если тест успешен
        """
        print("🧪 ТЕСТ ВВОДА С ПРОВЕРКОЙ РЕАЛЬНОСТИ")
        print("="*50)
        
        # Сначала проверяем что Comet реально открыт
        if not self.is_comet_really_open():
            print("❌ Comet не открыт! Сначала откройте его.")
            return False
        
        print("✅ Comet открыт, продолжаем тест...")
        
        # Тестируем ввод
        try:
            test_text = "REALITY_TEST_123"
            
            print(f"📝 Буду вводить текст: {test_text}")
            print("👀 Наблюдайте за окном Comet!")
            
            # Активация ассистента
            print("🔧 Alt+A...")
            pyautogui.hotkey('alt', 'a')
            await asyncio.sleep(1.5)
            
            # Ввод текста
            print("⌨️ Ввод текста...")
            pyautogui.typewrite(test_text, interval=0.1)
            await asyncio.sleep(1)
            
            # Enter
            print("⌨️ Enter...")
            pyautogui.press('enter')
            
            print("✅ Текст отправлен!")
            
            # Спрашиваем результат
            print(f"\n🤔 Что вы видите в ассистенте Comet?")
            print("1. Текст 'REALITY_TEST_123' появился")
            print("2. Текст появился частично")
            print("3. Текст не появился")
            print("4. Ассистент не открылся")
            
            try:
                import builtins
                answer = builtins.input("Ваш ответ (1-4): ")
                
                if answer == "1":
                    print("🎉 ОТЛИЧНО! Ввод работает в реальности!")
                    return True
                elif answer == "2":
                    print("⚠️ Частичный ввод")
                    return False
                elif answer == "3":
                    print("❌ Ввод не работает")
                    return False
                elif answer == "4":
                    print("❌ Ассистент не открылся")
                    return False
                else:
                    print("❓ Неизвестный результат")
                    return False
                    
            except Exception as e:
                logger.error(f"Ошибка получения ответа: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка теста: {e}")
            print(f"❌ Критическая ошибка: {e}")
            return False
    
    async def run_reality_check(self):
        """Запустить полную проверку реальности."""
        print("🔍 REALITY CHECK - Проверка реального состояния")
        print("="*60)
        print("🎯 Цель: убедиться что Comet реально открыт и работает")
        print("="*60)
        
        # Шаг 1: Проверка текущего состояния
        print(f"\n📊 ШАГ 1: Проверка текущего состояния")
        print("-"*40)
        
        is_open = self.is_comet_really_open()
        
        if is_open:
            print("✅ Comet уже открыт!")
            print("📝 Пропускаю ручное открытие")
        else:
            print("❌ Comet не открыт")
            
            # Шаг 2: Ручное открытие
            print(f"\n📊 ШАГ 2: Ручное открытие Comet")
            print("-"*40)
            
            if not await self.open_comet_manually():
                print("❌ Не удалось открыть Comet")
                return
        
        # Шаг 3: Тест ввода
        print(f"\n📊 ШАГ 3: Тест ввода с проверкой")
        print("-"*40)
        
        success = await self.test_input_with_real_check()
        
        # Итоги
        print(f"\n📊 ИТОГИ ПРОВЕРКИ РЕАЛЬНОСТИ")
        print("="*60)
        
        if success:
            print("🎉 ВСЕ РАБОТАЕТ В РЕАЛЬНОСТИ!")
            print("✅ Comet открыт")
            print("✅ Ввод работает")
            print("✅ Можно продолжать эксперименты")
        else:
            print("❌ ПРОБЛЕМЫ В РЕАЛЬНОСТИ:")
            print("❌ Comet не работает или ввод не работает")
            print("💡 Нужно решить проблемы с Comet")
        
        return success


async def main():
    """Главная функция."""
    session = RealityCheckSession()
    await session.run_reality_check()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Проверка прервана")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
