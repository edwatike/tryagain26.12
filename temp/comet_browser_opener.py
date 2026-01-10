"""
Программа для открытия браузера Comet на указанной странице и автоматической работы с ассистентом.

Использование:
    python temp/comet_browser_opener.py <URL> [prompt]
    python temp/comet_browser_opener.py  # запросит URL и промпт интерактивно
"""

import subprocess
import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional

# Попытка импортировать pyautogui для автоматизации клавиатуры
try:
    import pyautogui
    PYINPUT_AVAILABLE = True
except ImportError:
    PYINPUT_AVAILABLE = False
    print("ВНИМАНИЕ: pyautogui не установлен. Установите: pip install pyautogui")

# Попытка импортировать pyperclip для работы с буфером обмена
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except (ImportError, Exception) as e:
    PYPERCLIP_AVAILABLE = False
    print(f"ВНИМАНИЕ: pyperclip не доступен: {e}. Установите: pip install pyperclip")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальная переменная для режима отладки
DEBUG_MODE = True


def debug_print(message: str, debug_only: bool = False):
    """Выводит отладочное сообщение, если включен режим отладки."""
    if DEBUG_MODE or not debug_only:
        # Заменяем Unicode символы на ASCII для совместимости с Windows консолью
        message = message.replace('✓', '[OK]').replace('⚠', '[WARN]').replace('✗', '[FAIL]')
        print(f"[DEBUG] {message}")


def activate_browser_window(url: str, debug: bool = True) -> bool:
    """
    Активирует окно браузера Comet используя оба способа: pygetwindow и PowerShell.
    
    Args:
        url: URL страницы для поиска окна
        debug: Включить отладочный вывод
    
    Returns:
        True если окно активировано, False в противном случае
    """
    if debug:
        debug_print("Начинаю активацию окна браузера...")
    
    # Способ 1: pygetwindow
    try:
        import pygetwindow as gw
        debug_print("Способ 1: Поиск окна через pygetwindow...")
        
        # Ищем окно браузера по части названия
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            # Пробуем найти по URL в заголовке
            debug_print("Окно 'Comet' не найдено, ищу по URL...")
            all_windows = gw.getAllWindows()
            domain = url.split('//')[-1].split('/')[0]
            for win in all_windows:
                if 'Comet' in win.title or domain in win.title:
                    windows = [win]
                    debug_print(f"Найдено окно: {win.title}")
                    break
        
        if windows:
            window = windows[0]
            debug_print(f"Активирую окно: {window.title}")
            window.activate()
            time.sleep(1)  # Увеличиваем задержку для активации
            
            # Проверяем, что окно действительно активно
            if window.isActive:
                debug_print("✓ Окно активировано через pygetwindow")
                return True
            else:
                debug_print("⚠ Окно не стало активным через pygetwindow, пробую PowerShell...")
        else:
            debug_print("⚠ Окно не найдено через pygetwindow, пробую PowerShell...")
    except Exception as e:
        if debug:
            debug_print(f"Ошибка при активации через pygetwindow: {e}")
        debug_print("Пробую активировать через PowerShell...")
    
    # Способ 2: PowerShell
    try:
        debug_print("Способ 2: Активация окна через PowerShell...")
        domain = url.split('//')[-1].split('/')[0]
        
        # PowerShell команда для активации окна
        ps_command = f'''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {{
            [DllImport("user32.dll")]
            [return: MarshalAs(UnmanagedType.Bool)]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            
            [DllImport("user32.dll")]
            public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
        }}
"@
        $processes = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*Comet*" -or $_.MainWindowTitle -like "*{domain}*" }}
        if ($processes) {{
            $hwnd = $processes[0].MainWindowHandle
            [Win32]::SetForegroundWindow($hwnd)
            Write-Output "OK"
        }} else {{
            Write-Output "NOT_FOUND"
        }}
        '''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            debug_print("✓ Окно активировано через PowerShell")
            time.sleep(1)
            return True
        else:
            debug_print("⚠ Окно не найдено через PowerShell")
    except Exception as e:
        if debug:
            error_detail = f"Ошибка при активации через PowerShell: {type(e).__name__}: {e}"
            debug_print(error_detail)
    
    debug_print("✗ Не удалось активировать окно браузера")
    return False


def ensure_window_focused(debug: bool = True) -> bool:
    """
    Убеждается, что окно браузера в фокусе перед отправкой клавиш.
    
    Args:
        debug: Включить отладочный вывод
    
    Returns:
        True если окно в фокусе, False в противном случае
    """
    if debug:
        debug_print("Проверяю фокус окна...")
    
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'Comet' in win.title:
                    windows = [win]
                    break
        
        if windows:
            window = windows[0]
            if window.isActive:
                debug_print("✓ Окно в фокусе")
                return True
            else:
                debug_print("⚠ Окно не в фокусе, пытаюсь активировать...")
                window.activate()
                time.sleep(0.5)
                if window.isActive:
                    debug_print("✓ Окно активировано")
                    return True
    except Exception as e:
        if debug:
            error_detail = f"Ошибка при проверке фокуса: {type(e).__name__}: {e}"
            debug_print(error_detail)
    
    debug_print("⚠ Не удалось убедиться, что окно в фокусе")
    return False


def click_assistant_input(debug: bool = True) -> bool:
    """
    Кликает в поле ввода ассистента для активации фокуса.
    Поле ввода находится в правой части окна браузера, внизу панели ассистента.
    
    Args:
        debug: Включить отладочный вывод
    
    Returns:
        True если клик выполнен, False в противном случае
    """
    if not PYINPUT_AVAILABLE:
        return False
    
    if debug:
        debug_print("Кликаю в поле ввода ассистента...")
    
    try:
        import pygetwindow as gw
        # Находим окно браузера
        windows = gw.getWindowsWithTitle('Comet')
        if not windows:
            all_windows = gw.getAllWindows()
            for win in all_windows:
                if 'Comet' in win.title:
                    windows = [win]
                    break
        
        if not windows:
            if debug:
                debug_print("⚠ Окно браузера не найдено, использую координаты экрана")
            # Fallback: используем координаты экрана
            screen_width, screen_height = pyautogui.size()
            click_x = int(screen_width * 0.75)
            click_y = int(screen_height * 0.8)
        else:
            window = windows[0]
            # Поле ввода ассистента находится:
            # - В правой части окна (примерно 85-90% от ширины окна)
            # - В нижней части окна (примерно 85-90% от высоты окна)
            # Ассистент обычно занимает правую треть окна
            # Поле ввода ассистента находится в правой части окна, внизу
            # Кнопка отправки обычно справа от поля ввода
            click_x = window.left + int(window.width * 0.85)  # 85% от ширины окна (правая часть)
            click_y = window.top + int(window.height * 0.85)  # 85% от высоты окна (нижняя часть, где поле ввода)
            
            if debug:
                debug_print(f"Окно браузера: left={window.left}, top={window.top}, width={window.width}, height={window.height}")
        
        if debug:
            debug_print(f"Координаты клика в поле ввода ассистента: ({click_x}, {click_y})")
        
        # Кликаем в поле ввода
        pyautogui.click(click_x, click_y)
        time.sleep(1.5)  # Увеличиваем задержку для активации поля ввода
        
        if debug:
            debug_print("✓ Клик в поле ввода выполнен")
        return True
    except Exception as e:
        if debug:
            error_detail = f"Ошибка при клике в поле ввода: {type(e).__name__}: {e}"
            debug_print(error_detail)
        return False


def find_comet_browser() -> Optional[str]:
    """
    Ищет исполняемый файл браузера Comet в стандартных местах.
    
    Returns:
        Путь к исполняемому файлу или None, если не найден
    """
    # Возможные пути к браузеру Comet
    possible_paths = [
        # Perplexity Comet (приоритетный путь)
        os.path.expanduser(r"~\AppData\Local\Perplexity\Comet\Application\Comet.exe"),
        # Program Files (64-bit)
        r"C:\Program Files\Comet\Comet.exe",
        r"C:\Program Files (x86)\Comet\Comet.exe",
        # AppData (пользовательская установка)
        os.path.expanduser(r"~\AppData\Local\Comet\Application\Comet.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Comet\Comet.exe"),
        # Альтернативные пути
        r"C:\Program Files\Comet Browser\Comet.exe",
        r"C:\Program Files (x86)\Comet Browser\Comet.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Найден браузер Comet: {path}")
            return path
    
    logger.warning("Браузер Comet не найден в стандартных местах")
    return None


def open_comet_browser(url: str, browser_path: Optional[str] = None, prompt: Optional[str] = None, debug: bool = True) -> bool:
    """
    Открывает браузер Comet с указанным URL и автоматически открывает ассистента.
    
    Args:
        url: URL страницы для открытия
        browser_path: Путь к исполняемому файлу браузера (если None, будет выполнен поиск)
        prompt: Промпт для отправки ассистенту (если None, ассистент откроется, но промпт не будет отправлен)
    
    Returns:
        True если успешно, False в противном случае
    """
    # Нормализация URL (добавляем https:// если нет протокола)
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    if debug:
        debug_print(f"URL: {url}")
    
    # Поиск браузера, если путь не указан
    if browser_path is None:
        if debug:
            debug_print("Поиск браузера Comet...")
        browser_path = find_comet_browser()
        if browser_path is None:
            error_msg = "Не удалось найти браузер Comet. Укажите путь вручную."
            print(f"ОШИБКА: {error_msg}")
            logger.error(error_msg)
            return False
        if debug:
            debug_print(f"✓ Браузер найден: {browser_path}")
    
    if not os.path.exists(browser_path):
        error_msg = f"Файл браузера не найден: {browser_path}"
        print(f"ОШИБКА: {error_msg}")
        logger.error(error_msg)
        return False
    
    try:
        # Запуск браузера с URL
        print(f"Открываю браузер Comet: {url}")
        if debug:
            debug_print(f"Запуск процесса: {browser_path}")
        
        process = subprocess.Popen(
            [browser_path, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        
        if debug:
            debug_print(f"✓ Процесс браузера запущен (PID: {process.pid})")
        
        # Ждем загрузки страницы
        print("Ожидание загрузки страницы...")
        if debug:
            debug_print("Ожидание 5 секунд для загрузки страницы...")
        time.sleep(5)  # Увеличиваем время для полной загрузки
        
        # Открываем ассистента (Alt+A)
        if PYINPUT_AVAILABLE:
            # Настройка pyautogui
            # ВРЕМЕННО отключаем fail-safe для избежания ошибок при кликах
            # (fail-safe срабатывает, если мышь перемещается в угол экрана)
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.1
            
            if debug:
                debug_print("Настройка pyautogui завершена")
            
            # Активируем окно браузера
            if debug:
                debug_print("Активация окна браузера...")
            window_activated = activate_browser_window(url, debug=debug)
            
            if not window_activated:
                print("ПРЕДУПРЕЖДЕНИЕ: Не удалось активировать окно браузера. Продолжаю...")
                if debug:
                    debug_print("Попытка продолжить без активации окна...")
            else:
                if debug:
                    debug_print("✓ Проверка успешности: Окно браузера активировано")
            
            # Убеждаемся, что окно в фокусе
            if debug:
                debug_print("Проверка фокуса окна...")
            focus_ok = ensure_window_focused(debug=debug)
            if focus_ok:
                if debug:
                    debug_print("✓ Проверка успешности: Окно в фокусе")
            else:
                if debug:
                    debug_print("⚠ Проверка успешности: Не удалось убедиться, что окно в фокусе")
            
            print("Открываю ассистента (Alt+A)...")
            
            # КРИТИЧЕСКИ ВАЖНО: Убеждаемся, что окно точно в фокусе перед Alt+A
            if debug:
                debug_print("ШАГ 1: Активация окна браузера...")
            
            # Находим окно браузера
            try:
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle('Comet')
                if not windows:
                    all_windows = gw.getAllWindows()
                    for win in all_windows:
                        if 'Comet' in win.title:
                            windows = [win]
                            break
                
                if not windows:
                    print("ОШИБКА: Окно браузера не найдено!")
                    return False
                
                window = windows[0]
                if debug:
                    debug_print(f"Найдено окно: {window.title}")
                
                # Активируем окно
                if debug:
                    debug_print("Активация окна...")
                window.activate()
                time.sleep(1)  # Ждем активации
                
                # Проверяем, что окно активно
                if not window.isActive:
                    if debug:
                        debug_print("Окно не активно, пробую через PowerShell...")
                    # Пробуем через PowerShell
                    domain = url.split('//')[-1].split('/')[0]
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
                    $processes = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*Comet*" -or $_.MainWindowTitle -like "*{domain}*" }}
                    if ($processes) {{
                        $hwnd = $processes[0].MainWindowHandle
                        [Win32]::SetForegroundWindow($hwnd)
                    }}
                    '''
                    subprocess.run(['powershell', '-Command', ps_command], timeout=5)
                    time.sleep(1)
                
                if debug:
                    debug_print("✓ Окно активировано")
                
            except Exception as e:
                print(f"ОШИБКА при активации окна: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
                return False
            
            # КРИТИЧЕСКИ ВАЖНО: НЕ кликаем по сайту! Только Alt+A
            if debug:
                debug_print("ШАГ 2: Отправка Alt+A (БЕЗ кликов по сайту)...")
            
            # Способ 1: Через pyautogui.hotkey
            if debug:
                debug_print("Способ 1: pyautogui.hotkey('alt', 'a')...")
            pyautogui.hotkey('alt', 'a')
            time.sleep(0.5)
            
            # Способ 2: Через keyDown/keyUp (более надежно)
            if debug:
                debug_print("Способ 2: keyDown('alt') -> press('a') -> keyUp('alt')...")
            pyautogui.keyDown('alt')
            time.sleep(0.2)
            pyautogui.press('a')
            time.sleep(0.2)
            pyautogui.keyUp('alt')
            time.sleep(0.5)
            
            # Способ 3: Через win32api (если доступен)
            try:
                import win32api
                import win32con
                if debug:
                    debug_print("Способ 3: win32api (напрямую в активное окно)...")
                # Нажимаем Alt
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # VK_MENU = Alt
                time.sleep(0.1)
                # Нажимаем A
                win32api.keybd_event(ord('A'), 0, 0, 0)
                time.sleep(0.1)
                # Отпускаем A
                win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.1)
                # Отпускаем Alt
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                if debug:
                    debug_print("✓ win32api способ выполнен")
            except ImportError:
                if debug:
                    debug_print("win32api не доступен, пропускаю способ 3")
            except Exception as e:
                if debug:
                    debug_print(f"Ошибка в способе 3: {e}")
            
            # Ждем открытия ассистента (увеличиваем время для полной активации поля)
            if debug:
                debug_print("Ожидание открытия ассистента и активации поля ввода (3 секунды)...")
            time.sleep(3)
            
            if debug:
                debug_print("[OK] Все способы Alt+A выполнены")
                debug_print("ВАЖНО: Поле ввода должно быть активно по умолчанию!")
            
            # Если указан промпт - ПРОСТО: Ctrl+V → Enter (БЕЗ TAB, БЕЗ КЛИКОВ!)
            if prompt:
                print(f"Ввожу промпт: {prompt}")
                
                # ПРОСТО: Копируем → Вставляем → Enter (БЕЗ ЛИШНИХ ДЕЙСТВИЙ!)
                if PYPERCLIP_AVAILABLE:
                    if debug:
                        debug_print("Копирование промпта в буфер обмена...")
                    pyperclip.copy(prompt)
                    time.sleep(0.3)
                    
                    # Убеждаемся, что окно в фокусе перед Ctrl+V
                    if debug:
                        debug_print("Проверка фокуса окна перед вставкой...")
                    ensure_window_focused(debug=debug)
                    time.sleep(0.5)
                    
                    # СРАЗУ Ctrl+V (поле ввода УЖЕ активно!)
                    # Пробуем несколько способов для надежности
                    if debug:
                        debug_print("Вставка текста через Ctrl+V (поле ввода УЖЕ активно!)...")
                    
                    # Способ 1: pyautogui
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.3)
                    
                    # Способ 2: win32api (напрямую в активное окно)
                    try:
                        import win32api
                        import win32con
                        if debug:
                            debug_print("Дополнительная вставка через win32api...")
                        # Нажимаем Ctrl
                        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                        time.sleep(0.05)
                        # Нажимаем V
                        win32api.keybd_event(ord('V'), 0, 0, 0)
                        time.sleep(0.05)
                        # Отпускаем V
                        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
                        time.sleep(0.05)
                        # Отпускаем Ctrl
                        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                    except:
                        pass
                    
                    time.sleep(1.5)  # Задержка для вставки
                    
                    if debug:
                        debug_print("[OK] Команда Ctrl+V отправлена (несколько способов)")
                else:
                    print("ПРЕДУПРЕЖДЕНИЕ: pyperclip не доступен, использую обычный ввод")
                    pyautogui.write(prompt, interval=0.05)
                    time.sleep(1)
                
                # КРИТИЧЕСКИ ВАЖНО: Отправляем промпт СРАЗУ после вставки (без Tab!)
                print("Отправляю промпт...")
                if debug:
                    debug_print("Отправка промпта через Enter (СРАЗУ после вставки)...")
                
                # Задержка для обработки вставки - УВЕЛИЧИВАЕМ
                time.sleep(2)
                
                # Способ 1: Обычный Enter (несколько раз)
                if debug:
                    debug_print("Способ 1: pyautogui.press('enter') (первая попытка)...")
                pyautogui.press('enter')
                time.sleep(0.5)
                
                if debug:
                    debug_print("Способ 1: pyautogui.press('enter') (вторая попытка)...")
                pyautogui.press('enter')
                time.sleep(0.5)
                
                # Способ 2: Ctrl+Enter (часто используется в чатах)
                if debug:
                    debug_print("Способ 3: pyautogui.hotkey('ctrl', 'enter')...")
                pyautogui.hotkey('ctrl', 'enter')
                time.sleep(0.5)
                
                # Способ 4: win32api (Enter)
                try:
                    import win32api
                    import win32con
                    if debug:
                        debug_print("Способ 3: win32api (Enter)...")
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.2)
                    # Еще раз
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                except:
                    pass
                
                time.sleep(8)  # Увеличиваем задержку для начала ответа
                
                # ПРОВЕРКА: Убеждаемся, что промпт отправился
                # НЕ используем Tab для проверки - он переключает фокус!
                if debug:
                    debug_print("ПРОВЕРКА: Проверяю, что промпт отправился (без Tab!)...")
                time.sleep(2)  # Ждем обработки Enter
                
                print("Промпт отправлен! Ожидание ответа...")
                if debug:
                    debug_print("✓ Промпт отправлен, ожидание ответа ассистента...")
                
                # Ждем ответа от ассистента (увеличиваем время ожидания)
                print("Ожидание ответа ассистента (15 секунд)...")
                time.sleep(15)
                
                # Пытаемся скопировать ответ ассистента
                print("Копирую ответ ассистента...")
                if debug:
                    debug_print("Копирование ответа ассистента...")
                
                # Убеждаемся, что окно в фокусе
                ensure_window_focused(debug=debug)
                time.sleep(0.5)
                
                # КРИТИЧЕСКИ ВАЖНО: Копируем ответ ассистента
                # Пробуем прокрутить к ответу и скопировать его
                try:
                    import pygetwindow as gw
                    windows = gw.getWindowsWithTitle('Comet')
                    if not windows:
                        all_windows = gw.getAllWindows()
                        for win in all_windows:
                            if 'Comet' in win.title:
                                windows = [win]
                                break
                    if windows:
                        window = windows[0]
                        # Область ответа ассистента - ВЫШЕ, где начинается ответ (примерно 85% ширины, 25% высоты)
                        # НЕ внизу, где поле ввода!
                        response_x = window.left + int(window.width * 0.85)
                        response_y = window.top + int(window.height * 0.25)  # 25% от высоты (начало ответа)
                        if debug:
                            debug_print(f"Клик в область ответа ассистента (НЕ в поле ввода!): ({response_x}, {response_y})...")
                        
                        # Кликаем в область ответа (выше, где начинается ответ)
                        pyautogui.click(response_x, response_y)
                        time.sleep(1.5)  # Увеличиваем задержку для активации области ответа
                        
                        # ПРОСТО: Ctrl+A выделит текст ответа!
                        if debug:
                            debug_print("Выделение текста ответа через Ctrl+A...")
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.8)
                        
                        # Копируем выделенный текст
                        if debug:
                            debug_print("Копирование через Ctrl+C...")
                        pyautogui.hotkey('ctrl', 'c')
                        time.sleep(1.5)
                        
                except Exception as e:
                    if debug:
                        debug_print(f"Ошибка при копировании ответа: {e}")
                    # Fallback: просто Ctrl+A
                    if debug:
                        debug_print("Fallback: выделение всего текста через Ctrl+A...")
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.5)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(1.5)
                
                    # Получаем скопированный текст
                    if PYPERCLIP_AVAILABLE:
                        copied_text = pyperclip.paste()
                        print("\n" + "=" * 60)
                        print("Ответ ассистента:")
                        print("=" * 60)
                        # Показываем весь текст, но ограничиваем для читаемости
                        if len(copied_text) > 1000:
                            print(copied_text[:1000])
                            print(f"\n... (показано 1000 из {len(copied_text)} символов)")
                        else:
                            print(copied_text)
                        print("=" * 60)
                        
                        # ПРОВЕРКА: Если скопирован только промпт, пробуем еще раз
                        if copied_text.strip() == prompt.strip() or len(copied_text.strip()) < len(prompt.strip()) + 10:
                            if debug:
                                debug_print("ВНИМАНИЕ: Скопирован только промпт, а не ответ! Пробую еще раз...")
                            # Пробуем кликнуть выше (в начало ответа) и скопировать еще раз
                            try:
                                import pygetwindow as gw
                                windows = gw.getWindowsWithTitle('Comet')
                                if not windows:
                                    all_windows = gw.getAllWindows()
                                    for win in all_windows:
                                        if 'Comet' in win.title:
                                            windows = [win]
                                            break
                                if windows:
                                    window = windows[0]
                                    # Кликаем выше, где начинается ответ (25% высоты)
                                    response_x = window.left + int(window.width * 0.85)
                                    response_y = window.top + int(window.height * 0.25)
                                    if debug:
                                        debug_print(f"Повторный клик выше в область ответа: ({response_x}, {response_y})...")
                                    pyautogui.click(response_x, response_y)
                                    time.sleep(1)
                                    pyautogui.hotkey('ctrl', 'a')
                                    time.sleep(0.8)
                                    pyautogui.hotkey('ctrl', 'c')
                                    time.sleep(1.5)
                                    copied_text = pyperclip.paste()
                                    if debug:
                                        debug_print(f"Повторное копирование: получено {len(copied_text)} символов")
                            except Exception as e:
                                if debug:
                                    debug_print(f"Ошибка при повторном копировании: {e}")
                    
                    # Ищем ИНН и ссылку в тексте
                    import re
                    
                    # Улучшенный поиск ИНН (10 или 12 цифр, возможно с разделителями)
                    # Ищем паттерны типа "7721040281" или "7721-040-281" или "7721.040.281"
                    inn_patterns = [
                        r'\b\d{10}\b',  # 10 цифр подряд
                        r'\b\d{12}\b',  # 12 цифр подряд
                        r'\d{4}[-.\s]?\d{3}[-.\s]?\d{3}',  # 10 цифр с разделителями (например, 7721-040-281)
                        r'\d{4}[-.\s]?\d{4}[-.\s]?\d{4}',  # 12 цифр с разделителями
                        r'ИНН[:\s]+(\d{10,12})',  # ИНН: 7721040281
                        r'—\s*(\d{10,12})',  # — 7721040281
                    ]
                    
                    inns = []
                    for pattern in inn_patterns:
                        found = re.findall(pattern, copied_text, re.IGNORECASE)
                        # Обрабатываем результаты
                        for inn in found:
                            # Если это группа из regex (tuple), берем первый элемент
                            if isinstance(inn, tuple):
                                inn = inn[0] if inn[0] else inn[1] if len(inn) > 1 else str(inn)
                            # Очищаем от разделителей
                            cleaned_inn = re.sub(r'[-.\s]', '', str(inn))
                            if len(cleaned_inn) in [10, 12] and cleaned_inn not in inns:
                                inns.append(cleaned_inn)
                    
                    if inns:
                        # Берем первый найденный ИНН
                        found_inn = inns[0]
                        print(f"\n[OK] Найден ИНН: {found_inn}")
                        # Копируем ИНН в буфер обмена
                        pyperclip.copy(found_inn)
                        print(f"   ИНН скопирован в буфер обмена")
                    else:
                        print("\n[WARN] ИНН в ответе не найден")
                        if debug:
                            debug_print(f"Проверяемый текст (первые 500 символов): {copied_text[:500]}")
                    
                    # Улучшенные паттерны для поиска ссылок
                    url_patterns = [
                        r'https?://[^\s<>"{}|\\^`\[\]]+',  # Полные URL с протоколом
                        r'www\.[^\s<>"{}|\\^`\[\]]+',     # URL без протокола
                    ]
                    
                    all_urls = []
                    for pattern in url_patterns:
                        found = re.findall(pattern, copied_text)
                        all_urls.extend(found)
                    
                    # Убираем дубликаты и фильтруем
                    unique_urls = []
                    seen = set()
                    for url in all_urls:
                        # Нормализуем URL
                        url = url.rstrip('.,!?;:')  # Убираем знаки препинания в конце
                        if url.startswith('www.'):
                            url = 'https://' + url
                        if url not in seen and ('http' in url):
                            unique_urls.append(url)
                            seen.add(url)
                    
                    if unique_urls:
                        print(f"\n[OK] Найдено ссылок: {len(unique_urls)}")
                        for i, url in enumerate(unique_urls[:5], 1):  # Показываем первые 5
                            print(f"   {i}. {url}")
                        
                        # Копируем первую найденную ссылку
                        first_url = unique_urls[0]
                        pyperclip.copy(first_url)
                        print(f"\n[OK] Ссылка скопирована в буфер обмена: {first_url}")
                        print("   (Вы можете вставить её через Ctrl+V)")
                    else:
                        print("\n[WARN] Ссылки в ответе не найдены")
                        if debug:
                            debug_print(f"Проверяемый текст (первые 500 символов): {copied_text[:500]}")
                        print("   Попробуйте скопировать ссылку вручную из ответа ассистента")
                else:
                    print("[WARN] pyperclip не установлен, не могу прочитать ответ")
            else:
                print("Окно ассистента открыто. Введите промпт вручную.")
                if debug:
                    debug_print("Промпт не указан, ассистент открыт для ручного ввода")
        else:
            error_msg = "pyautogui не установлен. Браузер открыт, но ассистент не будет открыт автоматически."
            print(f"ВНИМАНИЕ: {error_msg}")
            print("Установите: pip install pyautogui")
            print("Или нажмите Alt+A вручную для открытия ассистента.")
            if debug:
                debug_print("PYINPUT_AVAILABLE = False")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем (Ctrl+C)")
        return False
    except Exception as e:
        error_msg = f"Ошибка при запуске браузера: {e}"
        print(f"\n{'=' * 60}")
        print(f"ОШИБКА: {error_msg}")
        print(f"{'=' * 60}")
        if debug:
            import traceback
            print("\nДетали ошибки:")
            traceback.print_exc()
            print(f"\n{'=' * 60}")
        logger.error(error_msg, exc_info=True)
        print("\nПопробуйте:")
        print("1. Проверить, что браузер Comet установлен")
        print("2. Закрыть другие окна, которые могут мешать")
        print("3. Запустить программу от имени администратора")
        print("4. Проверить логи выше для деталей")
        return False


def main():
    """Главная функция."""
    # Дефолтные значения
    DEFAULT_URL = "mc.ru"
    DEFAULT_PROMPT = "найди инн компании, ответом пришли номер, и ссылку откуда нашел"
    
    # Получение URL из аргументов командной строки или интерактивный ввод
    if len(sys.argv) > 1:
        url = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROMPT
    else:
        print()
        print("=" * 60)
        print("  Открытие браузера Comet с ассистентом")
        print("=" * 60)
        print()
        url_input = input(f"Введите адрес сайта (Enter для {DEFAULT_URL}): ").strip()
        url = url_input if url_input else DEFAULT_URL
        
        print()
        prompt_input = input(f"Введите промпт для ассистента (Enter для '{DEFAULT_PROMPT}'): ").strip()
        prompt = prompt_input if prompt_input else DEFAULT_PROMPT
    
    # Опциональный путь к браузеру из аргументов
    browser_path = None
    if len(sys.argv) > 3:
        browser_path = sys.argv[3]
    
    # Открытие браузера
    success = open_comet_browser(url, browser_path, prompt, debug=DEBUG_MODE)
    
    if success:
        print()
        print("Готово! Браузер открыт, ассистент активирован.")
        if prompt:
            print("Промпт отправлен.")
        print()
        print("Окно можно закрыть.")
        input("Нажмите Enter для выхода...")
        sys.exit(0)
    else:
        print()
        print("Ошибка: не удалось открыть браузер Comet")
        print()
        print("Возможные решения:")
        print("1. Убедитесь, что браузер Comet установлен")
        print("2. Проверьте путь: C:\\Users\\admin\\AppData\\Local\\Perplexity\\Comet\\Application\\Comet.exe")
        print("3. Установите pyautogui: pip install pyautogui")
        print()
        input("Нажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()

