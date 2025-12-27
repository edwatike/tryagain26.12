# Библия ошибок и решений

## Ошибка: NotImplementedError при запуске Playwright на Windows

### Описание проблемы
При запуске парсинга через Parser Service возникает ошибка:
```
NotImplementedError
Failed to connect to Chrome CDP at http://127.0.0.1:9222
```

Ошибка возникает при вызове `async_playwright().start()`, когда Playwright пытается создать subprocess для запуска драйвера.

### Причина
На Windows Playwright требует использования `WindowsProactorEventLoopPolicy` для asyncio, чтобы поддерживать subprocess. Проблема в том, что uvicorn.Server создает свой собственный event loop внутри `serve()`, который может не использовать установленную policy.

### Текущее состояние решения

**Попытки решения:**
1. ✅ Установка `WindowsProactorEventLoopPolicy` в `parser_service/run_api.py` ДО всех импортов
2. ✅ Установка policy в `parser_service/api.py` 
3. ✅ Использование `asyncio.run()` для запуска uvicorn сервера (как в `temp/test_browser_connection.py`, который работает)
4. ✅ Использование `uvicorn.Server` с явным указанием event loop

**Проблема:** Даже при использовании `asyncio.run()` uvicorn.Server создает свой event loop внутри `serve()`, который не использует установленную policy.

**Рабочее решение для тестов:**
`temp/test_browser_connection.py` работает, потому что использует `asyncio.run()` напрямую для тестовой функции, а не через uvicorn.

### Временное решение

Использовать `temp/test_browser_connection.py` как основу для тестирования парсера, или запускать парсинг в отдельном процессе с правильной event loop policy.

### Альтернативные решения для исследования

1. **Использовать синхронный API Playwright в отдельном потоке:**
   - Использовать `playwright.sync_api` вместо `playwright.async_api`
   - Запускать в отдельном потоке с собственным event loop

2. **Подключение к Chrome CDP напрямую через WebSocket:**
   - Избежать использования Playwright для запуска subprocess
   - Использовать WebSocket для подключения к Chrome CDP напрямую

3. **Использовать другой ASGI сервер:**
   - Попробовать Hypercorn или другой ASGI сервер, который может лучше работать с event loop policy

### Текущая конфигурация

**`parser_service/run_api.py`:**
```python
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def run_server():
    from api import app
    import uvicorn
    config = uvicorn.Config(app=app, host="127.0.0.1", port=9003, log_level="info", access_log=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_server())
```

### Дата последнего обновления
2025-12-26

### Решение (рабочее)

**Проблема:** uvicorn/Hypercorn создает event loop, который не использует `WindowsProactorEventLoopPolicy`, необходимую для Playwright subprocess.

**Решение:** Использовать подход из `temp/test_browser_connection.py` - запускать Playwright в отдельном потоке с собственным event loop через `asyncio.run()`.

#### Как работает решение:

1. **В `temp/test_browser_connection.py`** используется рабочий подход:
   - Устанавливается `WindowsProactorEventLoopPolicy` ДО импорта Playwright
   - Используется `asyncio.run()` напрямую для создания собственного event loop
   - Это позволяет Playwright создать subprocess без ошибки `NotImplementedError`

2. **В `parser_service/src/parser.py`** применен тот же подход:
   - На Windows Playwright запускается в отдельном потоке через `ThreadPoolExecutor`
   - В потоке устанавливается `WindowsProactorEventLoopPolicy`
   - Используется `asyncio.run()` для создания нового event loop с правильной policy
   - В этом loop запускается `async_playwright().start()` и подключение к Chrome CDP
   - Результат (playwright и browser объекты) возвращаются в основной поток

#### Код решения:

```python
# В parser_service/src/parser.py, метод connect_browser()
if sys.platform == 'win32':
    from concurrent.futures import ThreadPoolExecutor
    
    def run_playwright_in_thread(ws_url_param, chrome_cdp_url_param):
        """Run Playwright in a separate thread with its own event loop using asyncio.run()."""
        import asyncio
        import sys
        from playwright.async_api import async_playwright
        
        # Set event loop policy for this thread (same as test_browser_connection.py)
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        async def connect_playwright():
            playwright = await async_playwright().start()
            connect_url = ws_url_param if "ws://" in ws_url_param else chrome_cdp_url_param
            browser = await playwright.chromium.connect_over_cdp(connect_url)
            return playwright, browser
        
        # Use asyncio.run() to create a new event loop with the correct policy
        return asyncio.run(connect_playwright())
    
    # Run in thread pool executor
    current_loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="playwright")
    self.playwright, self.browser = await current_loop.run_in_executor(
        executor, run_playwright_in_thread, ws_url, self.chrome_cdp_url
    )
```

#### Проверка:

1. Запустить Parser Service:
   ```bash
   cd parser_service
   python run_api.py
   ```

2. Запустить тест парсинга:
   ```bash
   python temp/test_parser.py
   ```

3. Убедиться, что парсинг работает без `NotImplementedError`

### Статус
✅ Решение реализовано - используется подход из `test_browser_connection.py` с запуском Playwright в отдельном потоке

---

## Ошибка: Chrome запускается в headless режиме, парсер не подключается к видимому браузеру

### Описание проблемы
Парсер подключается к Chrome, но Chrome запущен в headless режиме (невидимый). В результате:
- Пользователь не видит окно браузера
- Невозможно решить CAPTCHA вручную
- Парсер не может работать с видимым браузером пользователя

При проверке через `curl http://127.0.0.1:9222/json/version` в User-Agent видно `HeadlessChrome`.

### Причина
Chrome был запущен в headless режиме (с флагом `--headless`) или подключился к неправильному процессу Chrome.

### Решение

1. **Остановить все процессы Chrome:**
   ```powershell
   Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
   ```

2. **Запустить Chrome в видимом режиме через скрипт:**
   ```bash
   start-chrome.bat
   ```
   
   Или вручную:
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --disable-gpu --no-sandbox --disable-dev-shm-usage
   ```
   
   **ВАЖНО:** НЕ используйте флаг `--headless`!

3. **Проверить, что Chrome запущен в видимом режиме:**
   ```bash
   python temp/check_chrome_mode.py
   ```
   
   Должно быть: `[OK] Chrome запущен в ВИДИМОМ режиме`
   
   Если видно `HeadlessChrome` в User-Agent - Chrome запущен неправильно.

4. **Убедиться, что окно Chrome видно:**
   - После запуска должно открыться окно Chrome
   - Если окна нет - Chrome запущен в headless режиме

5. **Перезапустить Parser Service** (если он уже запущен):
   ```bash
   # Остановить процессы на порту 9003
   netstat -ano | findstr ":9003"
   taskkill /F /PID <PID>
   
   # Запустить заново
   cd parser_service && python run_api.py
   ```

### Проверка
1. Проверить режим Chrome:
   ```bash
   curl http://127.0.0.1:9222/json/version
   ```
   
   В ответе `User-Agent` НЕ должен содержать `HeadlessChrome`.

2. Запустить парсинг через фронтенд и убедиться, что:
   - Окно Chrome видно
   - Парсер подключается к этому окну
   - При появлении CAPTCHA окно максимизируется для решения

### Измененные файлы
- `start-chrome.bat` - скрипт для запуска Chrome в видимом режиме
- `temp/check_chrome_mode.py` - скрипт для проверки режима Chrome

### Дата решения
2025-12-26

---

## Ошибка: OSError [Errno 22] Invalid argument при запуске Backend на Windows

### Описание проблемы
При запуске Backend API на Windows возникает ошибка:
```
OSError: [Errno 22] Invalid argument
```

Ошибка возникает в middleware при попытке использовать `print(..., file=sys.stderr)` или `logging.StreamHandler(sys.stderr)` в контексте uvicorn.

### Причина
На Windows в контексте uvicorn `sys.stderr` может быть закрыт или недоступен для записи, что вызывает `OSError: [Errno 22] Invalid argument`. Это происходит потому, что uvicorn управляет потоками ввода-вывода и может закрывать стандартные потоки.

### Решение

1. **Убрать все `print(..., file=sys.stderr)` из кода:**
   - Заменить на использование logger вместо print
   - Убрать явные handlers для `sys.stderr` из `logging.basicConfig()`

2. **Упростить настройку логирования:**
   - Не использовать `logging.StreamHandler(sys.stderr)` в `lifespan`
   - Позволить uvicorn самому управлять логированием
   - Использовать только стандартный logger без явных handlers

3. **Упростить логирование в middleware:**
   - Убрать избыточное debug-логирование
   - Обернуть логирование в try-except для безопасности

#### Код решения:

**В `backend/app/main.py`, функция `lifespan`:**
```python
# БЫЛО (вызывало ошибку):
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)  # ❌ Вызывало ошибку
    ],
    force=True
)

# СТАЛО (работает):
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # ✅ Позволяем uvicorn управлять handlers
)
```

**В `backend/app/main.py`, класс `CORSExceptionMiddleware`:**
```python
# БЫЛО (вызывало ошибку):
print(f"=== MIDDLEWARE: Request to {request.url.path} ===", file=sys.stderr, flush=True)  # ❌
logger.debug(f"=== MIDDLEWARE: Response status: {response.status_code} ===")  # ❌ Могло вызывать ошибку

# СТАЛО (работает):
# Убрано избыточное логирование, используется только необходимое
# Логирование обернуто в try-except для безопасности
```

### Проверка

1. **Проверить, что Backend запускается без ошибок:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

2. **Проверить health endpoint:**
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   
   Должен вернуть: `{"status":"ok"}`

3. **Проверить, что нет ошибок в логах:**
   - При запуске сервера не должно быть `OSError: [Errno 22] Invalid argument`
   - Все запросы должны обрабатываться корректно

### Измененные файлы
- `backend/app/main.py` - убраны все `print(..., file=sys.stderr)`, упрощена настройка logging

### Дата решения
2025-01-27

---

## Настройка Parser Service

### Описание
Parser Service - это отдельный сервис для парсинга веб-сайтов через Chrome CDP. Он работает на порту 9003 и требует запущенного Chrome с включенным remote debugging.

### Конфигурация портов

- **Parser Service**: порт 9003 (настраивается в `parser_service/run_api.py`)
- **Chrome CDP**: порт 9222 (настраивается в `parser_service/src/config.py`)
- **Backend ожидает**: `http://127.0.0.1:9003` (настраивается в `backend/app/config.py`)

### Запуск Chrome CDP

**ВАЖНО:** Chrome должен быть запущен в ВИДИМОМ режиме (не headless), чтобы можно было решить CAPTCHA вручную.

**Windows:**
```powershell
# Через скрипт
.\start-chrome.bat

# Или вручную
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --disable-gpu --no-sandbox --disable-dev-shm-usage
```

**ВАЖНО:** НЕ используйте флаг `--headless`!

### Запуск Parser Service

```powershell
cd parser_service
python run_api.py
```

Или через скрипт:
```powershell
.\start-parser.bat
```

### Проверка работоспособности

1. **Проверить Chrome CDP:**
   ```powershell
   Invoke-RestMethod http://127.0.0.1:9222/json/version
   ```
   Должен вернуть информацию о Chrome и WebSocket URL.

2. **Проверить Parser Service:**
   ```powershell
   Invoke-RestMethod http://127.0.0.1:9003/health
   ```
   Должен вернуть: `{"status":"ok"}`

3. **Полная диагностика:**
   ```powershell
   python temp/parser_service/diagnose_parser_full.py
   ```
   Скрипт проверит все компоненты и выполнит тестовый запрос на парсинг.

### Тестовый запрос на парсинг

```powershell
$body = @{ keyword = "кирпич"; max_urls = 5; source = "yandex" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:9003/parse -Method Post -ContentType "application/json; charset=utf-8" -Body $body
```

**ВАЖНО:** Используйте `Content-Type: application/json; charset=utf-8` для корректной обработки кириллицы.

### Известные проблемы и решения

#### Проблема: Кодировка кириллицы (Cyrillic mojibake)

**Симптом:** Запросы с кириллицей превращаются в `?????`

**Решение:** 
- Backend автоматически добавляет `Content-Type: application/json; charset=utf-8` в запросы к parser_service
- Если делаете запросы напрямую, обязательно указывайте charset

**Проверка:**
```powershell
# Правильно (с charset)
$body = @{ keyword = "кирпич" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:9003/parse -Method Post -ContentType "application/json; charset=utf-8" -Body $body

# Неправильно (без charset - может вызвать mojibake)
Invoke-RestMethod http://127.0.0.1:9003/parse -Method Post -ContentType "application/json" -Body $body
```

#### Проблема: Ошибка подключения к Chrome CDP

**Симптом:** `Cannot connect to Chrome CDP at http://127.0.0.1:9222`

**Решение:**
1. Убедитесь, что Chrome запущен с флагом `--remote-debugging-port=9222`
2. Проверьте, что Chrome не запущен в headless режиме
3. Проверьте доступность порта: `netstat -ano | findstr ":9222"`

**Проверка:**
```powershell
# Проверить доступность Chrome CDP
Invoke-RestMethod http://127.0.0.1:9222/json/version

# Проверить режим Chrome (не должен быть HeadlessChrome)
$response = Invoke-RestMethod http://127.0.0.1:9222/json/version
$response.User-Agent  # Не должно содержать "HeadlessChrome"
```

#### Проблема: Parser Service возвращает 503

**Симптом:** `503 Service Unavailable` при запросе к parser_service

**Причина:** Parser Service не может подключиться к Chrome CDP

**Решение:**
1. Убедитесь, что Chrome запущен с remote debugging
2. Проверьте, что порт 9222 доступен
3. Проверьте логи parser_service для деталей ошибки

#### Проблема: Chrome запущен, но CDP недоступен (Connection error: All connection attempts failed)

**Симптом:** 
- Ошибка: `Connection error in parse_keyword: Cannot connect to Chrome CDP at http://127.0.0.1:9222. Error: All connection attempts failed`
- Chrome запущен (видно в диспетчере задач), но порт 9222 не слушается
- `start-parser.bat` показывает: `[WARNING] Chrome CDP is not accessible on port 9222`

**Причина:** 
Chrome запущен БЕЗ флага `--remote-debugging-port=9222` или использует существующий профиль пользователя, который не поддерживает CDP. Обычно это происходит, если:
- Chrome был запущен обычным способом (без CDP)
- Chrome был запущен с другими параметрами
- Chrome был запущен до запуска `start-chrome.bat`
- Chrome пытается использовать существующий профиль пользователя, который уже занят другим процессом Chrome

**Решение:**

**Вариант 1 (Автоматический - Рекомендуемый):**
Все скрипты проекта (`start-chrome.bat`, `start-parser.bat`, `start-all.bat`) теперь автоматически:
1. Используют **единый профиль отладки** (`temp\chrome_debug_profile`)
2. Проверяют доступность Chrome CDP перед запуском
3. Автоматически запускают Chrome с CDP, если он не доступен
4. Используют централизованную конфигурацию из `scripts\chrome_config.bat`

**Вариант 2 (Ручной запуск):**
1. Закройте ВСЕ окна Chrome
2. Запустите `start-chrome.bat` - Chrome откроется с CDP на порту 9222 с единым профилем отладки
3. Или запустите Chrome вручную с правильными параметрами:
   ```cmd
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\tryagain\temp\chrome_debug_profile" --disable-gpu --no-sandbox --disable-dev-shm-usage
   ```

**Вариант 3 (Использование start-all.bat):**
`start-all.bat` автоматически проверяет доступность Chrome CDP:
- Если Chrome CDP доступен - не перезапускает его
- Если Chrome CDP недоступен - запускает Chrome с CDP и единым профилем

**Проверка:**
```cmd
# Проверить доступность Chrome CDP
curl http://127.0.0.1:9222/json/version

# Или использовать скрипт диагностики
scripts\check_chrome_cdp.bat

# Проверить, слушается ли порт 9222
netstat -ano | findstr ":9222"

# Проверить процессы Chrome
tasklist | findstr chrome.exe

# Проверить, какой профиль использует Chrome
wmic process where "name='chrome.exe'" get commandline | findstr user-data-dir
```

**Важно:**
- **Все скрипты используют ОДИН И ТОТ ЖЕ профиль** (`temp\chrome_debug_profile`) для обеспечения консистентности
- Если Chrome уже запущен без CDP, новый процесс Chrome с CDP может не запуститься из-за конфликта
- В этом случае нужно закрыть все окна Chrome и запустить его заново с CDP
- Chrome с CDP использует отдельный профиль отладки, чтобы избежать конфликтов с обычным Chrome

**Измененные файлы:**
- `scripts\chrome_config.bat` - централизованная конфигурация Chrome CDP (новый)
- `start-parser.bat` - использует единый профиль и централизованную конфигурацию
- `start-chrome.bat` - использует единый профиль и улучшенные проверки CDP
- `start-all.bat` - использует единый профиль и централизованную конфигурацию
- `stop-all.bat` - улучшена остановка Chrome с правильным профилем

**Дата решения:**
2025-12-26 (обновлено 2025-12-27)

#### Проблема: NotImplementedError на Windows

**Симптом:** `NotImplementedError` при запуске Playwright на Windows

**Решение:** Уже решено в коде - используется отдельный поток с `asyncio.run()` и `WindowsProactorEventLoopPolicy`. Если проблема сохраняется, проверьте:
1. Что используется правильная версия Python (3.12+)
2. Что все зависимости установлены: `pip install -r parser_service/requirements.txt`

### Порядок запуска сервисов

1. **Сначала** запустите Chrome CDP:
   ```powershell
   .\start-chrome.bat
   ```

2. **Затем** запустите Parser Service:
   ```powershell
   .\start-parser.bat
   ```

3. **Затем** запустите Backend:
   ```powershell
   .\start-backend.bat
   ```

4. **В последнюю очередь** запустите Frontend:
   ```powershell
   .\start-frontend.bat
   ```

### Диагностический скрипт

Для полной диагностики всех компонентов парсера используйте:
```powershell
python temp/parser_service/diagnose_parser_full.py
```

Скрипт проверит:
- Доступность Chrome CDP (порт 9222)
- Доступность Parser Service (порт 9003)
- Доступность Backend (порт 8000)
- Тестовый запрос на парсинг с кириллицей
- Интеграцию Backend с Parser Service

### Измененные файлы
- `backend/app/adapters/parser_client.py` - добавлен `Content-Type: application/json; charset=utf-8`
- `parser_service/src/parser.py` - улучшена обработка ошибок подключения к Chrome CDP
- `parser_service/api.py` - улучшена обработка ошибок с информативными сообщениями
- `temp/parser_service/diagnose_parser_full.py` - создан диагностический скрипт

### Дата настройки
2025-01-27

## Рекомендации по работе с Chrome CDP

### Общие рекомендации

1. **Всегда используйте единый профиль отладки:**
   - Все скрипты проекта используют один и тот же профиль: `temp\chrome_debug_profile`
   - Это обеспечивает консистентность и предотвращает конфликты
   - Профиль определяется в `scripts\chrome_config.bat`

2. **Используйте скрипты проекта для запуска Chrome:**
   - Не запускайте Chrome вручную без параметров CDP
   - Используйте `start-chrome.bat`, `start-parser.bat` или `start-all.bat`
   - Все скрипты автоматически проверяют доступность CDP перед запуском

3. **Проверяйте доступность CDP перед использованием:**
   - Используйте `scripts\check_chrome_cdp.bat` для диагностики
   - Или проверьте вручную: `curl http://127.0.0.1:9222/json/version`
   - Убедитесь, что Chrome запущен в видимом режиме (не headless) для возможности решения CAPTCHA

4. **При проблемах с Chrome CDP:**
   - Закройте все окна Chrome
   - Запустите `stop-all.bat` для полной остановки всех сервисов
   - Запустите `start-chrome.bat` для запуска Chrome с CDP
   - Проверьте доступность CDP через `scripts\check_chrome_cdp.bat`

5. **Централизованная конфигурация:**
   - Все параметры Chrome CDP находятся в `scripts\chrome_config.bat`
   - При необходимости изменить порт или путь к Chrome, обновите этот файл
   - Все скрипты автоматически используют эту конфигурацию

### Проверка работоспособности Chrome CDP

**Быстрая проверка:**
```cmd
scripts\check_chrome_cdp.bat
```

**Ручная проверка:**
```cmd
# Проверить доступность CDP
curl http://127.0.0.1:9222/json/version

# Проверить порт
netstat -ano | findstr ":9222"

# Проверить профиль Chrome
wmic process where "name='chrome.exe'" get commandline | findstr user-data-dir
```

**Ожидаемый результат:**
- CDP доступен на порту 9222
- Chrome запущен в видимом режиме (не headless)
- Chrome использует профиль `temp\chrome_debug_profile`
- WebSocket URL доступен для подключения

### Измененные файлы

- `scripts\chrome_config.bat` - централизованная конфигурация Chrome CDP
- `scripts\check_chrome_cdp.bat` - скрипт диагностики Chrome CDP
- `start-chrome.bat` - использует единый профиль и улучшенные проверки
- `start-parser.bat` - использует единый профиль и централизованную конфигурацию
- `start-all.bat` - использует единый профиль и централизованную конфигурацию
- `stop-all.bat` - улучшена остановка Chrome с правильным профилем

### Дата добавления рекомендаций
2025-12-27

---

## Ошибка: Парсинг возвращает старые результаты, реальный парсинг не выполняется

### Описание проблемы

**Симптом:**
- Парсинг запускается через Frontend или API, но возвращает старые результаты из базы данных
- В браузере Chrome не видно открытия вкладок с поисковиками (Google/Yandex)
- В истории браузера нет записей о посещении поисковиков
- Парсинг завершается мгновенно, но результаты идентичны предыдущим запускам
- Backend возвращает успешный ответ, но реальный парсинг не выполняется

**Пример:**
```bash
# Запуск парсинга
POST /parsing/start
{
  "keyword": "фланец",
  "depth": 2,
  "source": "google"
}

# Ответ успешный, но результаты старые
{
  "runId": "e35b244a-4b47-4f14-b71b-91123cff515a",
  "keyword": "фланец",
  "status": "running"
}

# Проверка результатов - те же 111 доменов, что и раньше
GET /domains/queue?parsingRunId=e35b244a-4b47-4f14-b71b-91123cff515a
# Возвращает старые данные из базы
```

### Причина

**Parser Service не запущен или недоступен:**
- Parser Service не запущен (порт 9003 не слушается)
- Backend не может подключиться к Parser Service
- Парсинг не выполняется реально, Backend возвращает старые данные из базы данных
- Chrome CDP может быть запущен, но Parser Service не работает

**Проверка:**
```cmd
# Проверить, слушается ли порт 9003
netstat -ano | findstr ":9003"

# Проверить доступность Parser Service
curl http://127.0.0.1:9003/health

# Если порт не слушается или health check не отвечает - Parser Service не запущен
```

### Решение

**Шаг 1: Проверить статус Parser Service**
```cmd
# Проверить порт
netstat -ano | findstr ":9003"

# Проверить health check
curl http://127.0.0.1:9003/health
```

**Шаг 2: Запустить Parser Service**

**Вариант 1 (Рекомендуемый - через скрипт):**
```cmd
cd parser_service
start-parser-service.bat
```

**Вариант 2 (Через start-all.bat):**
```cmd
start-all.bat
# Скрипт автоматически запустит все сервисы, включая Parser Service
```

**Вариант 3 (Вручную):**
```cmd
cd parser_service
python run_api.py
```

**Шаг 3: Проверить, что Parser Service запущен**
```cmd
# Должен вернуть {"status":"ok"}
curl http://127.0.0.1:9003/health

# Порт должен слушаться
netstat -ano | findstr ":9003"
```

**Шаг 4: Запустить парсинг заново**
После запуска Parser Service запустите парсинг снова. Теперь:
- В браузере Chrome должны открыться вкладки с поисковиками
- Парсинг будет выполняться реально
- Результаты будут новыми

### Проверка

**Успешный запуск Parser Service:**
```cmd
# Health check должен вернуть {"status":"ok"}
curl http://127.0.0.1:9003/health

# Порт должен слушаться
netstat -ano | findstr ":9003"
# Должен показать: TCP    127.0.0.1:9003         0.0.0.0:0              LISTENING       <PID>
```

**Успешный реальный парсинг:**
- В окне Chrome открываются вкладки с Google/Yandex поиском
- В истории браузера появляются записи о посещении поисковиков
- Парсинг занимает время (не мгновенный)
- Результаты новые (отличаются от предыдущих запусков)

### Важно

**Порядок запуска сервисов:**
1. **Сначала** Chrome CDP (`start-chrome.bat` или через `start-all.bat`)
2. **Затем** Parser Service (`start-parser-service.bat` или через `start-all.bat`)
3. **Затем** Backend (`start-backend.bat` или через `start-all.bat`)
4. **В последнюю очередь** Frontend (`start-frontend.bat` или через `start-all.bat`)

**Проверка перед парсингом:**
- Chrome CDP доступен: `curl http://127.0.0.1:9222/json/version`
- Parser Service доступен: `curl http://127.0.0.1:9003/health`
- Backend доступен: `curl http://127.0.0.1:8000/health`

### Измененные файлы

- `parser_service/start-parser-service.bat` - скрипт запуска Parser Service
- `start-all.bat` - автоматический запуск всех сервисов
- `start-parser.bat` - запуск Parser Service через общий скрипт

### Дата решения
2025-12-27

---

## Успех: Парсинг работает корректно в видимом режиме Chrome

### Описание успеха

**Что работает:**
- ✅ Chrome запускается в видимом режиме (не headless)
- ✅ Парсер подключается к Chrome через CDP
- ✅ Открываются вкладки с поисковиками (Google/Yandex) в окне Chrome
- ✅ Парсинг выполняется реально, собираются новые результаты
- ✅ Результаты сохраняются в базу данных
- ✅ Frontend может запускать парсинг через API

**Проверено:**
- Ключевое слово: "кирпич"
- Глубина: 1
- Источник: "google"
- Результат: найдено 119 доменов
- Вкладки с Google поиском открывались в браузере

### Текущая конфигурация

**Chrome CDP:**
- Порт: 9222
- Режим: видимый (не headless)
- Профиль: `temp\chrome_debug_profile` (единый для всех скриптов)
- Конфигурация: `scripts\chrome_config.bat`

**Parser Service:**
- Порт: 9003
- URL: `http://127.0.0.1:9003`
- Health check: `http://127.0.0.1:9003/health`

**Backend:**
- Порт: 8000
- URL: `http://127.0.0.1:8000`
- Parser Service URL: настраивается через `settings.parser_service_url`

### Известные ограничения

**⚠️ ТРЕБУЕТ РАБОТЫ: CAPTCHA**

**Проблема:**
- При парсинге Google/Yandex может появляться CAPTCHA
- Парсер ожидает, что пользователь решит CAPTCHA вручную в видимом окне Chrome
- Если CAPTCHA не решена в течение 5 минут - парсинг может завершиться с ошибкой

**Текущее поведение:**
- Парсер обнаруживает CAPTCHA и ждет до 5 минут
- Выводит сообщения в консоль: `[WAIT] GOOGLE: Waiting for CAPTCHA to be solved...`
- Пользователь должен вручную решить CAPTCHA в окне Chrome
- После решения CAPTCHA парсинг продолжается автоматически

**Что нужно сделать в будущем:**
- [ ] Интеграция с сервисами решения CAPTCHA (2captcha, anti-captcha и т.д.)
- [ ] Автоматическое определение и решение CAPTCHA
- [ ] Улучшенная обработка CAPTCHA с уведомлениями пользователю
- [ ] Возможность пропускать страницы с CAPTCHA и продолжать парсинг

**Приоритет:** Средний (парсинг работает, но требует ручного вмешательства при CAPTCHA)

### Дата фиксации успеха
2025-12-27
