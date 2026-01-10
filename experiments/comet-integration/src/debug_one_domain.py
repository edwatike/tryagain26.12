"""
Отладка на одном домене - выясняем почему не вводится промпт.
"""
import asyncio
import sys
import time
from pathlib import Path
import logging

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 1.0  # Увеличим паузу для отладки
    pyautogui.FAILSAFE = False
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.error("pyautogui не установлен!")

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


class DebugOneDomain:
    """Отладка на одном домене."""
    
    def __init__(self):
        logger.info("🔍 Отладочная сессия инициализирована")
    
    async def debug_comet_interaction(self):
        """Полная отладка взаимодействия с Comet."""
        print("🔍 ОТЛАДКА ВЗАИМОДЕЙСТВИЯ С COMET")
        print("="*60)
        print("🎯 Цель: выяснить почему не вводится промпт")
        print("📝 Домен: metallsnab-nn.ru")
        print("="*60)
        
        if not PYAUTOGUI_AVAILABLE:
            print("❌ pyautogui недоступен!")
            return
        
        print("\n⚠️  ВАЖНО:")
        print("   ✅ Откройте Comet браузер вручную")
        print("   ✅ Перейдите на любой сайт")
        print("   ✅ Не трогайте мышь/клавиатуру")
        print("   ✅ Наблюдайте за каждым шагом")
        print("\n🔧 Буду выполнять шаги с паузами для анализа")
        print("\nНажмите Enter для начала отладки...")
        input()
        
        try:
            # Шаг 1: Проверка окна
            await self.step1_check_window()
            
            # Шаг 2: Активация окна
            await self.step2_activate_window()
            
            # Шаг 3: Переход к домену
            await self.step3_navigate_to_domain()
            
            # Шаг 4: Активация ассистента
            await self.step4_activate_assistant()
            
            # Шаг 5: Проверка фокуса
            await self.step5_check_focus()
            
            # Шаг 6: Попытка ввода
            await self.step6_try_input()
            
            print("\n🎉 ОТЛАДКА ЗАВЕРШЕНА!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отладки: {e}")
    
    async def step1_check_window(self):
        """Шаг 1: Проверка окна Comet."""
        print(f"\n🔍 ШАГ 1: Проверка окна Comet")
        print("-"*40)
        
        if PYGETWINDOW_AVAILABLE:
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                window = windows[0]
                print(f"✅ Окно найдено: {window.title}")
                print(f"   Размер: {window.size}")
                print(f"   Позиция: {window.left}, {window.top}")
            else:
                print("❌ Окно 'Comet' не найдено!")
                print("   Доступные окна:")
                all_windows = gw.getAllWindows()
                for win in all_windows[:10]:  # Первые 10 окон
                    if 'comet' in win.title.lower():
                        print(f"   - {win.title}")
        else:
            print("⚠️ pygetwindow недоступен, предполагаем что Comet открыт")
        
        print("⏳ Пауза 3 секунды...")
        await asyncio.sleep(3)
    
    async def step2_activate_window(self):
        """Шаг 2: Активация окна."""
        print(f"\n🔍 ШАГ 2: Активация окна Comet")
        print("-"*40)
        
        print("🖱️ Попытка активировать окно...")
        
        if PYGETWINDOW_AVAILABLE:
            windows = gw.getWindowsWithTitle('Comet')
            if windows:
                windows[0].activate()
                print("✅ Окно активировано через pygetwindow")
            else:
                print("⚠️ Окно не найдено, пробую Alt+Tab...")
                await self._press_keys('alt', 'tab')
        else:
            print("⚠️ pygetwindow недоступен, пробую Alt+Tab...")
            await self._press_keys('alt', 'tab')
        
        print("⏳ Пауза 2 секунды...")
        await asyncio.sleep(2)
    
    async def step3_navigate_to_domain(self):
        """Шаг 3: Переход к домену."""
        print(f"\n🔍 ШАГ 3: Переход к домену")
        print("-"*40)
        
        domain = "metallsnab-nn.ru"
        url = f"https://{domain}"
        
        print(f"📍 Переход к: {domain}")
        print(f"🔗 URL: {url}")
        
        # Ctrl+L для адресной строки
        print("⌨️ Нажимаю Ctrl+L (адресная строка)...")
        await self._press_keys('ctrl', 'l')
        await asyncio.sleep(1)
        
        # Ввод URL
        print(f"⌨️ Ввожу URL: {url}")
        await self._type_text(url)
        await asyncio.sleep(1)
        
        # Enter
        print("⌨️ Нажимаю Enter...")
        await self._press_key('enter')
        
        print("⏳ Жду загрузки страницы 5 секунд...")
        await asyncio.sleep(5)
        
        print("✅ Страница загружена")
    
    async def step4_activate_assistant(self):
        """Шаг 4: Активация ассистента."""
        print(f"\n🔍 ШАГ 4: Активация ассистента")
        print("-"*40)
        
        print("⌨️ Нажимаю Alt+A (активация ассистента)...")
        await self._press_keys('alt', 'a')
        
        print("⏳ Жду 3 секунды...")
        await asyncio.sleep(3)
        
        print("✅ Ассистент активирован (надеюсь)")
    
    async def step5_check_focus(self):
        """Шаг 5: Проверка фокуса."""
        print(f"\n🔍 ШАГ 5: Проверка фокуса ввода")
        print("-"*40)
        
        print("🖱️ Пробую кликнуть в центр правой части экрана...")
        
        # Получаем размеры экрана
        screen_width, screen_height = pyautogui.size()
        click_x = int(screen_width * 0.8)  # 80% от ширины
        click_y = int(screen_height * 0.5)  # 50% от высоты
        
        print(f"🖱️ Клик в координаты: ({click_x}, {click_y})")
        pyautogui.click(click_x, click_y)
        
        print("⏳ Жду 1 секунду...")
        await asyncio.sleep(1)
        
        print("⌨️ Пробую Tab для перемещения фокуса...")
        await self._press_key('tab')
        await asyncio.sleep(1)
        
        print("⌨️ Еще раз Tab...")
        await self._press_key('tab')
        await asyncio.sleep(1)
        
        print("✅ Фокус должен быть установлен")
    
    async def step6_try_input(self):
        """Шаг 6: Попытка ввода."""
        print(f"\n🔍 ШАГ 6: Попытка ввода команды")
        print("-"*40)
        
        test_text = "/requisites"
        
        print(f"⌨️ Пытаюсь ввести: {test_text}")
        print("👀 СЛЕДИТЕ ЗА ЭКРАНОМ!")
        
        # Вводим по одной букве с паузой
        for i, char in enumerate(test_text):
            print(f"   Ввожу символ {i+1}: '{char}'")
            await self._type_text(char)
            await asyncio.sleep(0.5)
        
        print("⏳ Пауза 1 секунда...")
        await asyncio.sleep(1)
        
        print("⌨️ Нажимаю Enter...")
        await self._press_key('enter')
        
        print("⏳ Жду результат 10 секунд...")
        await asyncio.sleep(10)
        
        print("✅ Попытка ввода завершена")
        
        # Спрашиваем у пользователя что произошло
        print(f"\n🤔 АНАЛИЗ РЕЗУЛЬТАТА:")
        print("Что произошло на экране?")
        print("1. Текст успешно введен")
        print("2. Текст введен частично") 
        print("3. Текст не введен вообще")
        print("4. Что-то другое")
        print("\nВведите номер результата (1-4):")
        
        # Ждем ответ пользователя
        try:
            import builtins
            result = builtins.input("Результат: ")
            print(f"✅ Вы ввели: {result}")
            
            if result == "1":
                print("🎉 ОТЛИЧНО! Ввод работает!")
            elif result == "2":
                print("⚠️ Частичный ввод - нужно настроить тайминги")
            elif result == "3":
                print("❌ Ввод не работает - проблема с фокусом")
            else:
                print("❓ Неизвестный результат")
                
        except:
            print("⚠️ Не удалось получить ответ")
    
    async def _type_text(self, text: str):
        """Ввести текст."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.typewrite(text, interval=0.1)
    
    async def _press_key(self, key: str):
        """Нажать клавишу."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.press(key)
    
    async def _press_keys(self, *keys):
        """Нажать комбинацию."""
        if PYAUTOGUI_AVAILABLE:
            pyautogui.hotkey(*keys)


async def main():
    """Главная функция."""
    debugger = DebugOneDomain()
    await debugger.debug_comet_interaction()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Отладка прервана")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
