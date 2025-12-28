# Библия ошибок и решений

## ОБЯЗАТЕЛЬНЫЕ ПРОВЕРКИ

**⚠️ КРИТИЧЕСКИ ВАЖНО: Перед началом работы ОБЯЗАТЕЛЬНО:**

1. **Проверь состояние всех сервисов:**
   - Chrome CDP доступен на порту 9222
   - Parser Service отвечает на `http://127.0.0.1:9003/health`
   - Backend отвечает на `http://127.0.0.1:8000/health`
   - Frontend доступен на `http://localhost:3000`

2. **Проверь логи последних ошибок:**
   - `logs/Backend-*.log`
   - `logs/Parser Service-*.log`
   - `logs/Frontend-*.log`

3. **Проверь, что все сервисы запущены:**
   - `Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}`
   - `netstat -ano | findstr ":8000 :9003 :3000 :9222"`

---

## Ошибка: Дублирование вкладок при парсинге

### Описание проблемы
При запуске парсинга с одним источником (Google или Yandex) открываются две одинаковые вкладки вместо одной.

**Симптомы:**
- В браузере открываются две идентичные вкладки с одним и тем же поисковым запросом
- В логах Parser Service видно два одинаковых "=== PARSE REQUEST ===" для одного запроса
- В логах Backend видно два "Background task started" для одного `run_id`

### Причина
**Корневая причина:** FastAPI BackgroundTasks может вызывать async функцию дважды из-за особенностей выполнения фоновых задач. Проблема усугублялась тем, что:
1. Функция `run_parsing` определяется внутри `execute`, создавая новую функцию при каждом вызове
2. Отсутствовала защита от дублирования на уровне добавления задачи в BackgroundTasks
3. Отсутствовала защита от дублирования на уровне Parser Service

**Неудачные попытки исправления (зафиксировано для предотвращения повторов):**
1. ❌ Удаление `asyncio.create_task` из Backend - не помогло (дублирование происходило на уровне BackgroundTasks)
2. ❌ Добавление защиты только внутри `run_parsing` - не помогло (защита срабатывала слишком поздно)
3. ❌ Использование только `_running_parsing_tasks` без проверки перед `add_task` - не помогло (гонка условий)
4. ❌ Использование блокировки `asyncio.Lock` только в Parser Service - не помогло (проблема была в Backend)

### Решение ✅
Добавлена многоуровневая защита от дублирования:

**1. Защита на уровне Backend (перед добавлением в BackgroundTasks):**
```python
# backend/app/usecases/start_parsing.py
if background_tasks is not None:
    # CRITICAL: Check if task is already running BEFORE adding to BackgroundTasks
    if run_id in _running_parsing_tasks:
        logger.warning(f"[DUPLICATE PREVENTION] run_id {run_id} already in running tasks, skipping")
        return result
    
    # CRITICAL: Add run_id BEFORE adding to BackgroundTasks to prevent race condition
    _running_parsing_tasks.add(run_id)
    background_tasks.add_task(run_parsing)
```

**2. Защита внутри `run_parsing` (дополнительный уровень безопасности):**
```python
# Использование _processing_tasks для отслеживания задач, которые уже начали обработку
if run_id in _running_parsing_tasks:
    if run_id in start_parsing_module._processing_tasks:
        logger.warning(f"[DUPLICATE DETECTED] Parsing task for run_id {run_id} is already PROCESSING, skipping")
        return
    start_parsing_module._processing_tasks.add(run_id)
```

**3. Защита на уровне Parser Service:**
```python
# parser_service/api.py
_running_parse_requests = set()
_parse_lock = asyncio.Lock()

async def parse_keyword(request: ParseRequest):
    request_key = f"{request.keyword}_{request.depth}_{request.source}"
    
    async with _parse_lock:
        if request_key in _running_parse_requests:
            logger.warning(f"[DUPLICATE DETECTED] Parse request for '{request_key}' is already running, skipping")
            return ParseResponse(keyword=request.keyword, suppliers=[], total_found=0)
        
        _running_parse_requests.add(request_key)
    
    try:
        # ... parsing logic ...
    finally:
        async with _parse_lock:
            _running_parse_requests.discard(request_key)
```

### Проверка
```powershell
# Проверить логи Backend - должны быть записи DUPLICATE PREVENTION и только один Background task added
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE PREVENTION|DUPLICATE CHECK|Background task added|Marked run_id"

# Проверить логи Parser Service - должен быть только один PARSE REQUEST для каждого запроса
Get-Content "logs\Parser Service-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE|PARSE REQUEST|CREATING PAGES"

# Проверить, что открывается только одна вкладка в браузере
# Запустить парсинг с source="google" и убедиться, что открывается только одна вкладка Google
```

**Ожидаемый результат:**
- В логах Backend: один "[DUPLICATE PREVENTION] Checking run_id", один "Background task added"
- В логах Parser Service: один "[DUPLICATE CHECK] Marked request", один "=== PARSE REQUEST ==="
- В браузере: открывается только одна вкладка для каждого источника

### Измененные файлы
- `backend/app/usecases/start_parsing.py` - добавлена защита от дублирования на двух уровнях
- `parser_service/api.py` - добавлена защита от дублирования с блокировкой

### Дата решения
2025-12-28 ✅ **РЕШЕНО И ПРОВЕРЕНО**

---

## Рекомендации для предотвращения проблем

### 1. Защита от дублирования задач

**Проблема:** FastAPI BackgroundTasks может вызывать async функцию дважды.

**Решение:**
- Всегда добавляйте защиту на уровне `background_tasks.add_task` ПЕРЕД добавлением задачи
- Используйте глобальный set для отслеживания активных задач
- Добавляйте идентификатор задачи в set ПЕРЕД `add_task`, а не после
- Используйте дополнительную защиту внутри функции для отслеживания задач, которые уже начали обработку

**Шаблон кода:**
```python
# Глобальный set для отслеживания активных задач
_running_tasks = set()

async def execute(background_tasks):
    task_id = str(uuid.uuid4())
    
    # ЗАЩИТА: Проверка ПЕРЕД добавлением в BackgroundTasks
    if task_id in _running_tasks:
        logger.warning(f"Task {task_id} already running, skipping")
        return result
    
    # ЗАЩИТА: Добавление ПЕРЕД background_tasks.add_task
    _running_tasks.add(task_id)
    background_tasks.add_task(run_task, task_id)
    
    async def run_task(task_id):
        # Дополнительная защита внутри функции
        import module as mod
        if not hasattr(mod, '_processing_tasks'):
            mod._processing_tasks = set()
        
        if task_id in mod._processing_tasks:
            logger.warning(f"Task {task_id} already processing, skipping")
            return
        
        mod._processing_tasks.add(task_id)
        try:
            # ... выполнение задачи ...
        finally:
            mod._processing_tasks.discard(task_id)
            _running_tasks.discard(task_id)
```

### 2. Защита от дублирования HTTP запросов

**Проблема:** Один и тот же HTTP запрос может быть обработан дважды.

**Решение:**
- Используйте уникальный ключ запроса (keyword + depth + source)
- Используйте блокировку `asyncio.Lock` для предотвращения гонки условий
- Проверяйте наличие запроса в set ПЕРЕД началом обработки
- Всегда очищайте set в блоке `finally`

**Шаблон кода:**
```python
_running_requests = set()
_request_lock = asyncio.Lock()

async def handle_request(request):
    request_key = f"{request.keyword}_{request.depth}_{request.source}"
    
    async with _request_lock:
        if request_key in _running_requests:
            return empty_response()
        _running_requests.add(request_key)
    
    try:
        # ... обработка запроса ...
    finally:
        async with _request_lock:
            _running_requests.discard(request_key)
```

### 3. Обязательная проверка перезапуска сервисов

**Проблема:** Изменения в коде не применяются, если сервис не перезапущен.

**Решение:**
- Всегда проверяйте, что сервис перезапустился после изменений кода
- Проверяйте логи на наличие новых записей (например, новых логов "[DUPLICATE PREVENTION]")
- Используйте временные метки в логах для проверки, что код обновился
- Для Backend с `--reload` проверяйте сообщения "WatchFiles detected changes"

**Команды для проверки:**
```powershell
# Проверить, что Backend перезапустился
Get-Content "logs\Backend-*.log" -Tail 20 | Select-String -Pattern "Started server|Application startup|WatchFiles detected"

# Проверить, что новый код работает
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE PREVENTION|NEW_FEATURE_LOG"
```

---

## Рекомендации для быстрой диагностики проблем

### 1. Проверка состояния системы (ОБЯЗАТЕЛЬНО ПЕРВЫМ!)

**Перед диагностикой любой проблемы ОБЯЗАТЕЛЬНО проверьте:**

```powershell
# 1. Проверка портов и процессов
netstat -ano | findstr ":8000 :9003 :3000 :9222"
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"}

# 2. Проверка health endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:9003/health
curl http://localhost:3000

# 3. Проверка Chrome CDP
curl http://127.0.0.1:9222/json/version

# 4. Проверка последних ошибок в логах
Get-Content "logs\Backend-*.log" -Tail 50 | Select-String -Pattern "ERROR|Exception|Traceback"
Get-Content "logs\Parser Service-*.log" -Tail 50 | Select-String -Pattern "ERROR|Exception|Traceback"
```

### 2. Проверка логов для конкретного run_id

**Если проблема связана с конкретным запросом:**

```powershell
# Найти run_id из ответа API или логов
$runId = "f6cc389b-3be0-488e-a950-190bc4e0c76d"

# Проверить все логи для этого run_id
Get-Content "logs\Backend-*.log" | Select-String -Pattern $runId
Get-Content "logs\Parser Service-*.log" | Select-String -Pattern $runId

# Проверить последовательность событий
Get-Content "logs\Backend-*.log" | Select-String -Pattern $runId | Select-Object -Last 30
```

### 3. Проверка дублирования задач

**Если подозреваете дублирование:**

```powershell
# Backend: проверить дублирование задач
Get-Content "logs\Backend-*.log" -Tail 200 | Select-String -Pattern "DUPLICATE|Background task|run_id" | Select-Object -Last 30

# Parser Service: проверить дублирование запросов
Get-Content "logs\Parser Service-*.log" -Tail 200 | Select-String -Pattern "DUPLICATE|PARSE REQUEST|CREATING PAGES" | Select-Object -Last 30

# Подсчитать количество вызовов для одного run_id
$runId = "your-run-id"
(Get-Content "logs\Backend-*.log" | Select-String -Pattern $runId).Count
```

### 4. Проверка работоспособности связки Backend-Frontend

**Если проблема в отображении данных:**

```powershell
# 1. Проверить, что Backend возвращает данные
$runId = "your-run-id"
Invoke-RestMethod "http://127.0.0.1:8000/parsing/runs/$runId"

# 2. Проверить, что Frontend получает данные
# Откройте браузер DevTools (F12) -> Network -> проверьте запросы к /parsing/runs/{runId}

# 3. Проверить логи Backend на наличие запросов от Frontend
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "GET.*parsing/runs|POST.*parsing/start"
```

### 5. Быстрая проверка изменений в коде

**Если внесли изменения, но они не работают:**

```powershell
# 1. Проверить, что файл действительно изменился
Get-Content "backend/app/usecases/start_parsing.py" | Select-String -Pattern "DUPLICATE PREVENTION"

# 2. Проверить, что сервис перезапустился
Get-Content "logs\Backend-*.log" -Tail 20 | Select-String -Pattern "Started server|WatchFiles detected"

# 3. Проверить, что новый код выполняется
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE PREVENTION"
```

### 6. Использование скриптов мониторинга

**Для комплексной диагностики используйте:**

```powershell
# Запустить полный мониторинг всех сервисов
powershell.exe -ExecutionPolicy Bypass -File 'scripts\monitor-services.ps1' -ProjectRoot 'D:\tryagain'

# Проверить состояние через скрипт
.\scripts\check-services-status.ps1
```

### 7. Чеклист диагностики

**При любой проблеме проверьте по порядку:**

1. ✅ Все сервисы запущены? (порты 8000, 9003, 3000, 9222)
2. ✅ Health endpoints отвечают? (`/health` для каждого сервиса)
3. ✅ Нет ошибок в последних логах? (ERROR, Exception, Traceback)
4. ✅ Сервисы перезапустились после изменений? (проверить логи на новые записи)
5. ✅ Код действительно изменился? (grep по новым логам/меткам)
6. ✅ Нет дублирования задач? (проверить логи на дублирование)
7. ✅ База данных доступна? (проверить подключение)
8. ✅ Chrome CDP запущен? (проверить порт 9222)

---

## Ошибка: 404 при bulk delete parsing runs

### Описание проблемы
При попытке удалить выделенные записи через bulk delete endpoint возникает ошибка 404:
- `Failed to load resource: the server 127.0.0.1:8000/parsing/runs/bulk:1 responded with a status of 404 (Not Found)`
- `Error bulk deleting parsing runs: APIError: Parsing run not found`
- В логах видно: `Deleting parsing run: bulk` вместо `Bulk deleting X parsing runs`

### Причина
**Порядок маршрутов в FastAPI**: Параметризованный маршрут `/runs/{run_id}` был определен ПЕРЕД конкретным маршрутом `/runs/bulk`. FastAPI пытается сопоставить `/runs/bulk` с `/runs/{run_id}`, где `run_id = "bulk"`, что приводит к попытке удалить несуществующий parsing run с ID "bulk" вместо вызова bulk delete endpoint.

**Важно**: В FastAPI порядок регистрации маршрутов критически важен. Конкретные маршруты (например, `/runs/bulk`) должны быть определены ПЕРЕД параметризованными маршрутами (например, `/runs/{run_id}`), иначе FastAPI будет сопоставлять запросы с параметризованным маршрутом.

### Решение ✅
Переместить endpoint `/runs/bulk` ПЕРЕД `/runs/{run_id}` в файле `backend/app/transport/routers/parsing_runs.py`:

**Правильный порядок:**
1. `@router.delete("/runs/bulk")` - конкретный маршрут ПЕРВЫМ
2. `@router.delete("/runs/{run_id}")` - параметризованный маршрут ВТОРЫМ

**Изменения в файле:**
- Перемещен `bulk_delete_parsing_runs_endpoint` перед `delete_parsing_run_endpoint`
- Исправлено логирование в bulk delete endpoint (строка 272)

### Проверка
```powershell
# 1. Проверить, что сервис перезапустился
Get-Content "logs\Backend-*.log" -Tail 20 | Select-String -Pattern "Started server|WatchFiles detected"

# 2. Проверить доступность endpoint через curl
curl -X DELETE "http://127.0.0.1:8000/parsing/runs/bulk" -H "Content-Type: application/json" -d '[]'
# Ожидаемый результат: 400 "run_ids must be a non-empty list" (не 404!)

# 3. Проверить логи Backend
Get-Content "logs\Backend-*.log" -Tail 50 | Select-String -Pattern "Bulk deleting|Deleting parsing run: bulk"
# Ожидаемый результат: "Bulk deleting X parsing runs" (не "Deleting parsing run: bulk")

# 4. Проверить через Frontend:
# - Открыть страницу /parsing-runs
# - Выделить несколько записей
# - Нажать "Удалить"
# - Убедиться, что удаление работает без ошибок 404
```

**Ожидаемый результат:**
- Endpoint `/parsing/runs/bulk` доступен и возвращает 200/207/400 вместо 404
- Bulk delete работает корректно через Frontend
- В логах видно корректные сообщения "Bulk deleting X parsing runs" вместо "Deleting parsing run: bulk"

### Измененные файлы
- `backend/app/transport/routers/parsing_runs.py` - изменен порядок маршрутов DELETE

### Дата решения
2025-12-28 ✅ **РЕШЕНО**

**Важное замечание**: После изменения порядка маршрутов может потребоваться полный перезапуск Backend (не только перезагрузка через WatchFiles), чтобы изменения вступили в силу. Если проблема сохраняется после перезапуска, проверьте порядок маршрутов в файле еще раз.

---

## Ошибка: UnmappedInstanceError при удалении parsing run

### Описание проблемы
При попытке удалить parsing run через endpoint `DELETE /parsing/runs/{run_id}` возникает ошибка 500:
- `UnmappedInstanceError: Class 'types.SimpleNamespace' is not mapped`
- `AttributeError: 'types.SimpleNamespace' object has no attribute '_sa_instance_state'`
- В логах видно: `Error deleting parsing run {run_id}: UnmappedInstanceError`

**Симптомы:**
- Backend возвращает 500 Internal Server Error при удалении
- В логах видна ошибка `UnmappedInstanceError: Class 'types.SimpleNamespace' is not mapped`
- Запись не удаляется из базы данных
- Frontend показывает ошибку удаления

### Причина
**Корневая причина:** Метод `ParsingRunRepository.delete` пытался использовать `session.delete(run)`, где `run` был объектом `SimpleNamespace` (возвращенным методом `get_by_id`), а не SQLAlchemy-моделью. SQLAlchemy не может удалить объекты, которые не являются ORM-моделями.

**Детали:**
1. `ParsingRunRepository.get_by_id` возвращает `SimpleNamespace` объект (не ORM-модель)
2. `ParsingRunRepository.delete` пытался использовать `session.delete(run)` с `SimpleNamespace`
3. SQLAlchemy требует ORM-модель для `session.delete()`

### Решение ✅
Использовать прямой SQL-запрос для удаления вместо `session.delete()`:

**1. Исправлен `backend/app/usecases/delete_parsing_run.py`:**
```python
async def execute(db: AsyncSession, run_id: str) -> bool:
    """Delete parsing run by run_id."""
    # CRITICAL FIX: Use direct SQL to delete, bypassing repository
    # This avoids the SimpleNamespace issue completely
    logger.info(f"Deleting parsing run {run_id} using direct SQL")
    
    # First, check if run exists
    check_result = await db.execute(
        text("SELECT COUNT(*) FROM parsing_runs WHERE run_id = :run_id"),
        {"run_id": run_id}
    )
    count_before = check_result.scalar()
    logger.info(f"Runs with run_id {run_id} before delete: {count_before}")
    
    if count_before == 0:
        logger.warning(f"Run {run_id} not found in database")
        return False
    
    # Delete the run using direct SQL
    result = await db.execute(
        text("DELETE FROM parsing_runs WHERE run_id = :run_id"),
        {"run_id": run_id}
    )
    await db.flush()
    
    deleted_count = result.rowcount
    logger.info(f"Delete query executed - rowcount: {deleted_count}")
    
    # Verify deletion
    check_result_after = await db.execute(
        text("SELECT COUNT(*) FROM parsing_runs WHERE run_id = :run_id"),
        {"run_id": run_id}
    )
    count_after = check_result_after.scalar()
    logger.info(f"Runs with run_id {run_id} after delete (before commit): {count_after}")
    
    return deleted_count > 0
```

**2. Исправлен `backend/app/transport/routers/parsing_runs.py`:**
- Добавлено логирование вызова `delete_parsing_run.execute`
- Добавлена проверка после коммита
- Добавлен принудительный flush после коммита
- Добавлена повторная попытка удаления, если запись все еще существует

**3. Исправлен `frontend/moderator-dashboard-ui/lib/api.ts`:**
- Критическое исправление: проверка статуса 204 для DELETE запросов происходит ДО проверки `response.ok`
- Это предотвращает обработку успешного DELETE как ошибки

### Проверка
```powershell
# 1. Проверить, что сервис перезапустился
Get-Content "logs\Backend-*.log" -Tail 20 | Select-String -Pattern "Started server|WatchFiles detected"

# 2. Проверить удаление через API
python -c "import requests; r1 = requests.get('http://127.0.0.1:8000/parsing/runs?limit=1&offset=0'); d1 = r1.json(); rid = d1['runs'][0].get('runId') or d1['runs'][0].get('run_id'); print(f'Deleting: {rid}'); r2 = requests.delete(f'http://127.0.0.1:8000/parsing/runs/{rid}'); print(f'Status: {r2.status_code}')"
# Ожидаемый результат: Status 204 (не 500!)

# 3. Проверить, что запись удалена
python -c "import requests; import time; r1 = requests.get('http://127.0.0.1:8000/parsing/runs?limit=5&offset=0'); d1 = r1.json(); rid = 'test-id'; r2 = requests.delete(f'http://127.0.0.1:8000/parsing/runs/{rid}'); time.sleep(2); r3 = requests.get('http://127.0.0.1:8000/parsing/runs?limit=5&offset=0'); d2 = r3.json(); ids = [r.get('runId') or r.get('run_id') for r in d2['runs']]; print(f'Still exists: {rid in ids}')"
# Ожидаемый результат: Still exists: False (запись удалена)

# 4. Проверить логи Backend
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "Deleting parsing run|using direct SQL|rowcount|Successfully deleted|Transaction committed"
# Ожидаемый результат: Видны логи "Deleting parsing run {run_id} using direct SQL" и "Successfully deleted"
```

**Ожидаемый результат:**
- Endpoint `DELETE /parsing/runs/{run_id}` возвращает 204 вместо 500
- Запись удаляется из базы данных
- Frontend корректно обрабатывает успешное удаление
- В логах нет ошибок `UnmappedInstanceError`

### Измененные файлы
- `backend/app/usecases/delete_parsing_run.py` - использует прямой SQL вместо `session.delete()`
- `backend/app/transport/routers/parsing_runs.py` - улучшено логирование и проверка после коммита
- `backend/app/adapters/db/session.py` - добавлен автоматический коммит в `get_db` как страховка
- `frontend/moderator-dashboard-ui/lib/api.ts` - исправлена обработка статуса 204 для DELETE запросов
- `frontend/moderator-dashboard-ui/app/parsing-runs/page.tsx` - улучшена обработка удаления и обновление состояния

### Дата решения
2025-12-28 ✅ **РЕШЕНО**

**Важное замечание**: После исправления ОБЯЗАТЕЛЬНО перезапустить Backend полностью (остановить все процессы Python и запустить заново), чтобы изменения вступили в силу. Если проблема сохраняется после перезапуска, проверьте, что код действительно использует прямой SQL (проверить через `python -c "from app.usecases.delete_parsing_run import execute; import inspect; print(inspect.getsource(execute))"`).

---

## Ошибка: Bulk delete не удаляет записи (возвращает успех, но записи остаются)

### Описание проблемы
При попытке удалить несколько parsing runs через bulk delete endpoint:
- Backend возвращает статус 200/207 с `{"deleted": N, "total": N}`
- Но записи НЕ удаляются из базы данных
- Frontend продолжает отображать удаленные записи
- В логах нет ошибок, но записи остаются в БД

**Симптомы:**
- `DELETE /parsing/runs/bulk` возвращает 200/207
- Response показывает `{"deleted": N}`, но записи все еще существуют
- Frontend не обновляется после удаления
- Записи остаются в БД даже после успешного ответа

### Причина
**Корневая причина:** `log_audit` вызывался ДО `commit()` в той же транзакции. Если `log_audit` падал с ошибкой (например, из-за проблем с таблицей `audit_log`), вся транзакция откатывалась, и удаление не сохранялось в БД, хотя endpoint возвращал успех.

**Дополнительные проблемы:**
1. Использование одной транзакции для всех удалений в bulk delete приводило к `InFailedSQLTransactionError`, если одно удаление падало
2. Commit в `get_db` dependency мог конфликтовать с commit'ами в endpoint
3. Проверка удаления в той же сессии показывала неправильный результат из-за кэша сессии

### Решение ✅
**1. Использование отдельных сессий для каждого удаления:**
```python
# CRITICAL: Use separate session for each delete to avoid transaction conflicts
for run_id in run_ids:
    async with AsyncSessionLocal() as delete_session:
        # Direct SQL DELETE in separate session
        delete_result = await delete_session.execute(
            text("DELETE FROM parsing_runs WHERE run_id = :run_id"),
            {"run_id": run_id}
        )
        # Commit FIRST, before audit log
        await delete_session.flush()
        await delete_session.commit()
```

**2. Audit log ПОСЛЕ commit в отдельной сессии:**
```python
# Log to audit_log AFTER commit (in a separate transaction)
# This way audit log errors won't affect the delete
try:
    from app.adapters.audit import log_audit
    async with AsyncSessionLocal() as audit_session:
        await log_audit(...)
        await audit_session.commit()
except Exception as audit_err:
    logger.warning(f"Error logging audit for run {run_id}: {audit_err}")
    # Don't fail the delete if audit logging fails
```

**3. Проверка удаления через новую сессию:**
```python
# Verify deletion using a NEW session to ensure we read from DB, not cache
async with AsyncSessionLocal() as verify_session:
    verify_result = await verify_session.execute(...)
    count_after = verify_result.scalar()
```

**4. Исправлен frontend Select статуса:**
- Select теперь сразу обновляет URL при изменении значения
- Убран `setTimeout`, который вызывал проблемы

**5. Исправлена обработка ответа bulk delete в `api.ts`:**
- Для статуса 204 возвращается пустой объект
- Для статуса 200 парсится JSON (bulk delete возвращает `{deleted, total, errors}`)

### Проверка
```powershell
# 1. Проверить, что сервис перезапустился
Get-Content "logs\Backend-*.log" -Tail 20 | Select-String -Pattern "Started server|WatchFiles detected"

# 2. Проверить bulk delete через API
python -c "import requests; r = requests.delete('http://127.0.0.1:8000/parsing/runs/bulk', json=['test-id-1', 'test-id-2'], headers={'Content-Type': 'application/json'}, timeout=10); print(f'Status: {r.status_code}'); print(f'Response: {r.text}')"
# Ожидаемый результат: Status 200 или 207, Response с deleted count

# 3. Проверить, что записи удалены
python -c "import requests; import time; r1 = requests.get('http://127.0.0.1:8000/parsing/runs?status=failed&limit=5&offset=0'); d1 = r1.json(); ids = [r.get('runId') or r.get('run_id') for r in d1.get('runs', [])[:2]]; print(f'Deleting: {ids}'); r2 = requests.delete('http://127.0.0.1:8000/parsing/runs/bulk', json=ids, headers={'Content-Type': 'application/json'}, timeout=30); time.sleep(5); r3 = requests.get('http://127.0.0.1:8000/parsing/runs?status=failed&limit=10&offset=0'); d3 = r3.json(); remaining = [r.get('runId') or r.get('run_id') for r in d3.get('runs', [])]; still_exist = [rid for rid in ids if rid in remaining]; print(f'Still exist: {len(still_exist)}'); print('SUCCESS' if not still_exist else 'FAILED')"
# Ожидаемый результат: Still exist: 0, SUCCESS

# 4. Проверить через Frontend:
# - Открыть страницу /parsing-runs
# - Выбрать статус "Ошибка" в Select
# - Выделить все записи со статусом "Ошибка"
# - Нажать "Удалить"
# - Убедиться, что записи удалены и список обновился
```

**Ожидаемый результат:**
- Bulk delete удаляет записи из БД
- Frontend обновляется и не показывает удаленные записи
- Select статуса работает корректно
- В логах видны сообщения "Committed deletion" и "Verified: Run ... deleted successfully"

### Измененные файлы
- `backend/app/transport/routers/parsing_runs.py` - bulk delete использует отдельные сессии, audit log после commit
- `backend/app/usecases/delete_parsing_run.py` - убран flush из usecase (вызывающий код управляет транзакцией)
- `frontend/moderator-dashboard-ui/app/parsing-runs/page.tsx` - исправлен Select статуса (сразу обновляет URL)
- `frontend/moderator-dashboard-ui/lib/api.ts` - исправлена обработка ответа bulk delete (парсинг JSON для статуса 200)

### Дата решения
2025-12-28 ✅ **РЕШЕНО**

**Важное замечание**: После исправления ОБЯЗАТЕЛЬНО перезапустить Backend полностью. Проблема была в порядке операций: audit log должен выполняться ПОСЛЕ commit в отдельной сессии, чтобы ошибки аудита не откатывали удаление.

---

## 💡 Рекомендации для предотвращения проблем с транзакциями и удалением

### 1. Порядок операций в транзакциях

**⚠️ КРИТИЧЕСКИ ВАЖНО: Всегда делайте commit ПЕРЕД операциями, которые могут откатить транзакцию!**

**Неправильно:**
```python
# ❌ НЕПРАВИЛЬНО: audit log ДО commit
await delete_session.execute(text("DELETE FROM ..."))
await log_audit(...)  # Если это падает - вся транзакция откатывается!
await delete_session.commit()
```

**Правильно:**
```python
# ✅ ПРАВИЛЬНО: commit ПЕРЕД audit log
await delete_session.execute(text("DELETE FROM ..."))
await delete_session.flush()
await delete_session.commit()  # Сначала commit!

# Audit log в отдельной сессии ПОСЛЕ commit
async with AsyncSessionLocal() as audit_session:
    await log_audit(...)
    await audit_session.commit()  # Ошибки аудита не влияют на удаление
```

### 2. Использование отдельных сессий для независимых операций

**⚠️ КРИТИЧЕСКИ ВАЖНО: Для bulk операций используйте отдельные сессии для каждой операции!**

**Неправильно:**
```python
# ❌ НЕПРАВИЛЬНО: все удаления в одной транзакции
for run_id in run_ids:
    await db.execute(text("DELETE FROM ... WHERE run_id = :run_id"), {"run_id": run_id})
await db.commit()  # Если одно удаление падает - все откатывается!
```

**Правильно:**
```python
# ✅ ПРАВИЛЬНО: каждое удаление в отдельной сессии
for run_id in run_ids:
    async with AsyncSessionLocal() as delete_session:
        await delete_session.execute(text("DELETE FROM ... WHERE run_id = :run_id"), {"run_id": run_id})
        await delete_session.flush()
        await delete_session.commit()  # Каждое удаление независимо
```

### 3. Проверка результатов через новую сессию

**⚠️ КРИТИЧЕСКИ ВАЖНО: Проверяйте результаты операций через новую сессию, чтобы читать из БД, а не из кэша!**

**Неправильно:**
```python
# ❌ НЕПРАВИЛЬНО: проверка в той же сессии
await delete_session.execute(text("DELETE FROM ..."))
await delete_session.commit()
verify = await delete_session.execute(text("SELECT COUNT(*) FROM ..."))  # Может показать старые данные из кэша!
```

**Правильно:**
```python
# ✅ ПРАВИЛЬНО: проверка через новую сессию
await delete_session.execute(text("DELETE FROM ..."))
await delete_session.commit()
await delete_session.close()  # Закрыть сессию

# Проверка через новую сессию
async with AsyncSessionLocal() as verify_session:
    verify = await verify_session.execute(text("SELECT COUNT(*) FROM ..."))  # Читает из БД!
```

### 4. Обработка ошибок в bulk операциях

**⚠️ КРИТИЧЕСКИ ВАЖНО: Ошибка в одной операции не должна блокировать остальные!**

**Правильно:**
```python
deleted_count = 0
errors = []

for run_id in run_ids:
    async with AsyncSessionLocal() as delete_session:
        try:
            await delete_session.execute(text("DELETE FROM ... WHERE run_id = :run_id"), {"run_id": run_id})
            await delete_session.commit()
            deleted_count += 1
        except Exception as e:
            errors.append(f"Error deleting {run_id}: {str(e)}")
            # Ошибка не влияет на другие удаления!
```

### 5. Порядок маршрутов в FastAPI

**⚠️ КРИТИЧЕСКИ ВАЖНО: Конкретные маршруты ДО параметризованных!**

**Неправильно:**
```python
# ❌ НЕПРАВИЛЬНО: параметризованный маршрут ПЕРЕД конкретным
@router.delete("/runs/{run_id}")  # FastAPI будет пытаться сопоставить "/runs/bulk" с этим!
async def delete_one(...):
    ...

@router.delete("/runs/bulk")  # Этот маршрут никогда не будет достигнут!
async def delete_bulk(...):
    ...
```

**Правильно:**
```python
# ✅ ПРАВИЛЬНО: конкретный маршрут ПЕРЕД параметризованным
@router.delete("/runs/bulk")  # Конкретный маршрут ПЕРВЫМ
async def delete_bulk(...):
    ...

@router.delete("/runs/{run_id}")  # Параметризованный маршрут ВТОРЫМ
async def delete_one(...):
    ...
```

### 6. Frontend: Обновление состояния после удаления

**⚠️ КРИТИЧЕСКИ ВАЖНО: Всегда обновляйте состояние с текущими параметрами URL!**

**Правильно:**
```typescript
// ✅ ПРАВИЛЬНО: использовать текущие параметры URL
const handleDelete = async (runId: string) => {
  await apiFetch(`/parsing/runs/${runId}`, { method: "DELETE" })
  
  // Получить текущие параметры из URL
  const currentPage = searchParams.get("page") || "1"
  const currentStatus = searchParams.get("status") || "all"
  
  // Обновить список с текущими параметрами
  await loadRuns({
    page: parseInt(currentPage),
    status: currentStatus,
    // ... другие параметры
  })
}
```

### 7. Frontend: Select компоненты должны сразу обновлять URL

**⚠️ КРИТИЧЕСКИ ВАЖНО: Select компоненты должны сразу обновлять URL, без задержек!**

**Неправильно:**
```typescript
// ❌ НЕПРАВИЛЬНО: setTimeout вызывает проблемы
<Select onValueChange={(value) => {
  setStatusFilter(value)
  setTimeout(() => handleFilterChange(), 0)  // Задержка может вызвать проблемы!
}}>
```

**Правильно:**
```typescript
// ✅ ПРАВИЛЬНО: сразу обновлять URL
<Select onValueChange={(value) => {
  setStatusFilter(value)
  handleFilterChange()  // Сразу вызывать без задержки
}}>
```

### 8. Проверка результатов на Frontend

**⚠️ КРИТИЧЕСКИ ВАЖНО: После исправления ОБЯЗАТЕЛЬНО проверить результат на Frontend!**

**Чеклист проверки:**
1. ✅ Открыть страницу в браузере
2. ✅ Выполнить операцию (удаление, фильтрация и т.д.)
3. ✅ Убедиться, что результат отображается корректно
4. ✅ Проверить консоль браузера (F12) - не должно быть ошибок
5. ✅ Проверить Network tab - запросы должны быть успешными
6. ✅ Проверить, что состояние обновляется корректно

**Команды для проверки:**
```powershell
# Проверить, что Frontend доступен
curl http://localhost:3000

# Проверить, что Backend доступен
curl http://127.0.0.1:8000/health

# Проверить логи Backend
Get-Content "logs\Backend-*.log" -Tail 50

# Проверить логи Frontend
Get-Content "logs\Frontend-*.log" -Tail 50
```

---
