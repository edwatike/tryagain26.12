# Спецификация проекта B2B Platform

**⚠️ КРИТИЧЕСКИ ВАЖНО: Этот документ отражает ТОЛЬКО проверенное и рабочее состояние системы.**

**📚 Связанные документы:**
- **Главная инструкция**: [`docs/MASTER_INSTRUCTION.md`](MASTER_INSTRUCTION.md) - архитектура, запуск, настройка
- **Библия ошибок**: [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md) - **НАЧИНАЙ ОТСЮДА при диагностике**
- **Критические точки**: [`docs/CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md`](CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md) - критические точки интеграции
- **Правила работы**: [`.cursorrules`](../.cursorrules)

**Правила обновления:**
1. **Спецификация обновляется ТОЛЬКО после успешной проверки работоспособности**
2. **Перед добавлением в спецификацию - ОБЯЗАТЕЛЬНАЯ проверка через тесты или ручное тестирование**
3. **Если что-то не работает - это должно быть помечено как "НЕ РАБОТАЕТ" или "ТРЕБУЕТ ПРОВЕРКИ"**
4. **При исправлении ошибки - сначала проверяем, потом обновляем спецификацию**

**🔍 Статус проверки:**
- ✅ Проверено и работает
- ⚠️ Требует проверки
- ❌ Не работает / Известная проблема
- 🔧 В процессе исправления

---

**Примечание:** Архитектура системы, структура проекта, запуск и настройка описаны в [`docs/MASTER_INSTRUCTION.md`](MASTER_INSTRUCTION.md). Этот документ содержит только детальную спецификацию API и рабочих связок Backend-Frontend.

---

## 1. Архитектура Backend

### 1.1 Структура модулей

Backend организован по принципу Clean Architecture с разделением на слои:

**`app/transport/`** - HTTP слой:
- `routers/` - FastAPI endpoints (только маршрутизация, валидация входных данных)
- `schemas/` - Pydantic схемы (DTO) для валидации запросов и ответов

**`app/usecases/`** - Бизнес-логика:
- Независимые от HTTP функции бизнес-логики
- Каждый usecase имеет функцию `execute()` с параметрами
- Используют репозитории и адаптеры для работы с БД и внешними сервисами

**`app/adapters/`** - Внешние сервисы:
- `parser_client.py` - HTTP клиент для Parser Service (отправка запросов на `/parse`)
- `checko_client.py` - HTTP клиент для Checko API (получение данных о компаниях)
- `db/` - работа с БД:
  - `models.py` - SQLAlchemy модели (таблицы БД)
  - `repositories.py` - репозитории для работы с моделями
  - `session.py` - управление сессиями БД

**`app/config.py`** - Конфигурация:
- Загрузка переменных окружения через Pydantic Settings
- Настройки подключения к БД, Parser Service, Checko API

### 1.2 Модели БД и связи

**Основные таблицы:**

1. **`moderator_suppliers`** - поставщики
   - Связи: `supplier_keywords` (many-to-many через `SupplierKeywordModel`)
   - Поля: id, name, inn, domain, type, checko_data (сжатый JSON), и др.

2. **`keywords`** - ключевые слова
   - Связи: `supplier_keywords` (many-to-many)
   - Поля: id, keyword (unique), created_at

3. **`supplier_keywords`** - связь поставщиков и ключевых слов (junction table)
   - Foreign Keys: `supplier_id` → `moderator_suppliers.id` (ON DELETE CASCADE)
   - Foreign Keys: `keyword_id` → `keywords.id` (ON DELETE CASCADE)
   - Поля: supplier_id, keyword_id, url_count, parsing_run_id, first_url

4. **`parsing_requests`** - запросы на парсинг
   - Поля: id, title, raw_keys_json, source, depth, created_at

5. **`parsing_runs`** - запуски парсинга
   - Foreign Keys: `request_id` → `parsing_requests.id` (ON DELETE CASCADE)
   - Поля: id, run_id (unique), request_id, status, depth, source, process_log (JSON)

6. **`domains_queue`** - очередь доменов для обработки
   - Поля: id, domain, keyword, url, parsing_run_id, source, status
   - Unique Constraint: (domain, keyword, parsing_run_id)

7. **`blacklist`** - черный список доменов
   - Поля: domain (PK), reason, added_at, parsing_run_id

8. **`audit_log`** - журнал аудита изменений
   - Поля: id, table_name, operation, record_id, old_data, new_data, changed_by, created_at

### 1.3 Основные API endpoints

**Роутеры из `backend/app/transport/routers/`:**

- `health.py` - проверка работоспособности (`GET /health`)
- `moderator_suppliers.py` - управление поставщиками (`/moderator/suppliers`)
- `keywords.py` - управление ключевыми словами (`/keywords`)
- `blacklist.py` - управление черным списком (`/moderator/blacklist`)
- `parsing.py` - запуск парсинга (`/parsing/start`, `/parsing/status`)
- `parsing_runs.py` - история парсинга и логи (`/parsing/runs`)
- `domains_queue.py` - очередь доменов (`/domains`)
- `checko.py` - интеграция с Checko API (`/moderator/checko/{inn}`)
- `attachments.py` - вложения (`/attachments`)

### 1.4 Взаимодействие Frontend-Backend

**Все HTTP запросы идут через `frontend/moderator-dashboard-ui/lib/api.ts`:**

- Функции API используют `apiFetch<T>()` для всех запросов
- Типы данных определены в `lib/types.ts` и соответствуют Pydantic схемам Backend
- Обработка ошибок через класс `APIError`
- Retry механизм для временных ошибок (503, 504, network errors)

**Основные функции API:**
- `getSuppliers()`, `getSupplier()`, `createSupplier()`, `updateSupplier()`, `deleteSupplier()`
- `getKeywords()`, `createKeyword()`, `deleteKeyword()`
- `getBlacklist()`, `addToBlacklist()`, `removeFromBlacklist()`
- `startParsing()`, `getParsingStatus()`, `getParsingRuns()`, `getParsingRun()`, `getParsingLogs()`
- `getDomainsQueue()`, `removeFromDomainsQueue()`
- `getCheckoData()`

### 1.5 Взаимодействие Backend-Parser Service

**Backend → Parser Service:**

1. **Запрос парсинга:**
   - `ParserClient.parse()` отправляет `POST /parse` на Parser Service
   - Параметры: keyword, depth, source (google/yandex/both), run_id
   - Content-Type: `application/json; charset=utf-8` (для корректной обработки кириллицы)

2. **Health check:**
   - `ParserClient.health_check()` отправляет `GET /health` на Parser Service

**Parser Service → Chrome CDP:**

1. Parser Service подключается к Chrome CDP через `http://127.0.0.1:9222`
2. Создает вкладки для поиска (одна вкладка на источник: google/yandex)
3. Выполняет поиск и извлекает ссылки с результатов
4. Возвращает список доменов и ссылок

**Parser Service → Backend:**

1. После завершения парсинга Parser Service возвращает результат в ответе
2. Backend сохраняет домены в `domains_queue` и обновляет статус `parsing_runs`
3. Parser Service может отправлять логи через `PUT /parsing/runs/{run_id}/logs` (если реализовано)

**Защита от дублирования:**
- Parser Service использует `request_key = f"{keyword}_{depth}_{source}"` для предотвращения дублирования
- Backend использует `_running_parsing_tasks` для отслеживания запущенных задач

---

## 2. API Endpoints (Backend)

**⚠️ ВАЖНО: Этот раздел описывает ОЖИДАЕМОЕ поведение. Реальная работоспособность каждого endpoint должна быть проверена и помечена статусом.**

### 2.1 Базовые правила

**Ожидаемое поведение:**
- Все endpoints возвращают JSON
- Все ошибки возвращают JSON с полем `detail`
- CORS заголовки добавляются ко ВСЕМ ответам (включая ошибки)
- Все даты в ответах - строки в формате ISO (`YYYY-MM-DD`)

**Статус проверки:**
- ✅ CORS заголовки работают (исправлено в Ошибке 3, TROUBLESHOOTING.md)
- ✅ Обработка ошибок с CORS работает (исправлено в Ошибке 3)
- ⚠️ **ТРЕБУЕТ ПРОВЕРКИ:** Все endpoints на реальных данных с реальной БД
- ⚠️ **ТРЕБУЕТ ПРОВЕРКИ:** Все edge cases и валидация параметров

### 2.2 Suppliers (Поставщики)

**Базовый путь:** `/moderator/suppliers`

**Статус проверки:**
- ✅ Исправлены ошибки с импортом `date` (Ошибка 4)
- ✅ Исправлена конвертация `date` → `string` (Ошибка 2)
- ⚠️ **ТРЕБУЕТ ПРОВЕРКИ:** Все CRUD операции на реальных данных
- ⚠️ **ТРЕБУЕТ ПРОВЕРКИ:** Пагинация, фильтры, валидация параметров

#### `GET /moderator/suppliers`
Список поставщиков с пагинацией.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000) - количество записей
- `offset` (int, default=0, min=0) - смещение
- `type` (string, optional) - фильтр по типу (`supplier` или `reseller`)

**Response:**
```json
{
  "suppliers": [
    {
      "id": 1,
      "name": "ООО Компания",
      "inn": "1234567890",
      "email": "info@company.ru",
      "domain": "company.ru",
      "registrationDate": "2005-07-15",  // ISO string
      // ... другие поля
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

**Особенности:**
- Поле `registrationDate` ВСЕГДА строка в формате ISO, НЕ объект `date`
- Конвертация `date` → `string` происходит в роутере ПЕРЕД валидацией DTO
- Используется `from_attributes=False` при валидации

#### `GET /moderator/suppliers/{supplier_id}`
Получить поставщика по ID.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Path параметры:**
- `supplier_id` (int) - ID поставщика

**Response:** `ModeratorSupplierDTO`

**Ошибки:**
- `404` - поставщик не найден

#### `POST /moderator/suppliers`
Создать нового поставщика.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Request body:** `CreateModeratorSupplierRequestDTO`

**Response:** `ModeratorSupplierDTO` (status 201)

#### `PUT /moderator/suppliers/{supplier_id}`
Обновить поставщика.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Path параметры:**
- `supplier_id` (int) - ID поставщика

**Request body:** `UpdateModeratorSupplierRequestDTO` (camelCase)

**Особенности:**
- Backend конвертирует camelCase → snake_case для БД
- Маппинг полей: `companyStatus` → `company_status`, `registrationDate` → `registration_date`

**Response:** `ModeratorSupplierDTO`

**Ошибки:**
- `404` - поставщик не найден

#### `DELETE /moderator/suppliers/{supplier_id}`
Удалить поставщика.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Path параметры:**
- `supplier_id` (int) - ID поставщика

**Response:** `204 No Content`

**Ошибки:**
- `404` - поставщик не найден

#### `GET /moderator/suppliers/{supplier_id}/keywords`
Получить keywords поставщика.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ** (исправлена ошибка с NaN в Ошибке 5, но требует проверки на реальных данных)

**Path параметры:**
- `supplier_id` (int) - ID поставщика (ВАЛИДНЫЙ, не NaN)

**Response:**
```json
{
  "keywords": [
    {
      "keyword": "сантехника",
      "urlCount": 10,
      "runId": "uuid-string",
      "firstUrl": "https://example.com"
    }
  ]
}
```

**Ошибки:**
- `422` - если `supplier_id` невалидный (NaN, не число, <= 0) - исправлено в Frontend (Ошибка 5)
- `404` - поставщик не найден

### 2.3 Checko API (Интеграция с Checko.ru)

**Базовый путь:** `/moderator/checko`

**Статус проверки:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-30)

#### `GET /moderator/checko/{inn}`

Получить данные о компании из Checko API.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-30)

**Path параметры:**
- `inn` (string) - ИНН компании (10 или 12 цифр)

**Query параметры:**
- `force_refresh` (bool, optional, default=false) - принудительное обновление данных (игнорировать кэш)

**Response:** `CheckoDataResponse`

**Особенности:**
- Backend кэширует данные Checko в БД на 24 часа
- Если данные свежие (менее 24 часов) - возвращаются из БД без запроса к Checko API
- Если `force_refresh=true` - данные обновляются из Checko API независимо от кэша
- Данные сжимаются через gzip перед сохранением в БД (поле `checko_data` типа BYTEA)

**Пример запроса:**
```powershell
# Получить данные Checko для ИНН
curl "http://127.0.0.1:8000/moderator/checko/4703148343"

# Принудительное обновление
curl "http://127.0.0.1:8000/moderator/checko/4703148343?force_refresh=true"
```

**Пример ответа:**
```json
{
  "name": "ООО СТРОЙТОРГОВЛЯ",
  "inn": "4703148343",
  "ogrn": "1174704000767",
  "kpp": "470301001",
  "companyStatus": "Действующая",
  "registrationDate": "2017-11-04",
  "legalAddress": "188643, Ленинградская область, Всеволожский район...",
  "phone": "+7 (812) 123-45-67",
  "website": "https://example.com",
  "revenue": 150000000,
  "profit": 5000000,
  "financeYear": 2023,
  "legalCasesCount": 10,
  "legalCasesSum": 50000000,
  "legalCasesAsPlaintiff": 5,
  "legalCasesAsDefendant": 5,
  "checkoData": "{\"_finances\": {...}, \"_legal\": {...}, ...}"
}
```

**Связка Backend-Frontend:**

**1. Загрузка данных Checko:**
```typescript
// frontend/moderator-dashboard-ui/lib/api.ts
export async function getCheckoData(inn: string, forceRefresh?: boolean): Promise<CheckoDataResponse> {
  const url = `/moderator/checko/${inn}${forceRefresh ? '?force_refresh=true' : ''}`
  return apiFetch<CheckoDataResponse>(url)
}
```

**2. Использование в форме редактирования:**
```typescript
// frontend/moderator-dashboard-ui/app/suppliers/[id]/edit/supplier-edit-client.tsx
// При нажатии "Заполнить Данные"
const checkoResponse = await getCheckoData(formData.inn, false)
// Автоматическое заполнение формы
setFormData({
  ...formData,
  name: checkoResponse.name || formData.name,
  ogrn: checkoResponse.ogrn || null,
  // ... все Checko поля
})
```

**3. Использование в карточке поставщика:**
```typescript
// frontend/moderator-dashboard-ui/components/supplier-card.tsx
// При нажатии "Загрузить данные Checko"
const checkoResponse = await getCheckoData(supplier.inn, false)
// Обновление поставщика с данными Checko
const updatedSupplier = await updateSupplier(supplier.id, {
  // ... все Checko поля
  checkoData: checkoResponse.checkoData || null,
})
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/suppliers/{id}/edit`
2. Ввести ИНН (например: `4703148343`)
3. Нажать "Заполнить Данные"
4. Проверить, что поля автоматически заполняются данными из Checko
5. Сохранить - данные должны сохраниться в БД
6. Открыть карточку поставщика - данные должны отображаться
7. Нажать "Загрузить данные Checko" - данные должны обновиться (если прошло более 24 часов)

**Ожидаемый результат:**
- Данные Checko загружаются и отображаются корректно
- Кэширование работает (не делается лишних запросов к Checko API)
- Все Checko поля сохраняются в БД
- Данные отображаются в карточке поставщика

**Ошибки:**
- `404` - компания с таким ИНН не найдена в Checko
- `422` - невалидный ИНН (не 10 или 12 цифр)
- `500` - ошибка при запросе к Checko API или обработке данных

### 2.4 Keywords (Ключевые слова)

**Базовый путь:** `/keywords`

**Статус проверки:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

#### `GET /keywords`
Список всех keywords.

**Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

**Response:**
```json
{
  "keywords": [
    {
      "id": 1,
      "keyword": "сантехника",
      "createdAt": "2025-12-26T10:00:00Z"
    }
  ]
}
```

#### `POST /keywords`
Создать keyword.

**Request body:**
```json
{
  "keyword": "сантехника"
}
```

**Response:** `KeywordDTO` (status 201)

#### `DELETE /keywords/{keyword_id}`
Удалить keyword.

**Path параметры:**
- `keyword_id` (int) - ID keyword

**Response:** `204 No Content`

**Ошибки:**
- `404` - keyword не найден

### 2.4 Parsing (Парсинг)

**Базовый путь:** `/parsing`

**Статус проверки:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-28)

**⚠️ ВАЖНО: ТРЕБУЕТ РАБОТЫ НАД CAPTCHA** - см. раздел "Известные ограничения" ниже

#### `POST /parsing/start`
Запустить парсинг.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-28)

**✅ ИСПРАВЛЕНО: Дублирование вкладок** - добавлена многоуровневая защита от дублирования задач парсинга. Теперь при запуске парсинга с одним источником (google/yandex) открывается только одна вкладка.

**Request body:**
```json
{
  "keyword": "кирпич",
  "depth": 2,
  "source": "google"
}
```

**Параметры:**
- `keyword` (string, required) - ключевое слово для поиска
- `depth` (int, default=10) - количество страниц результатов поиска для парсинга (глубина)
- `source` (string, default="google") - источник поиска: `"google"`, `"yandex"`, или `"both"`

**Response (201 Created):**
```json
{
  "runId": "4f468e53-9ec5-4c03-aebf-04c54bdf5477",
  "keyword": "кирпич",
  "status": "running"
}
```

**Как работает связка Backend-Frontend:**

**1. Frontend отправляет запрос:**

```typescript
// frontend/moderator-dashboard-ui/app/manual-parsing/page.tsx
async function handleStart() {
  const data = await apiFetch<{ runId: string; keyword: string; status: string }>("/parsing/start", {
    method: "POST",
    body: JSON.stringify({ keyword, depth, source }),
  })
  router.push(`/parsing-runs/${data.runId}`)
}
```

**2. Backend обрабатывает запрос:**

```python
# backend/app/transport/routers/parsing.py
@router.post("/start", status_code=201)
async def start_parsing_endpoint(
    request: StartParsingRequestDTO,
    db: AsyncSession = Depends(get_db)
):
    """Start parsing for a keyword."""
    # Validate source
    valid_sources = ["google", "yandex", "both"]
    source = request.source.lower() if request.source else "google"
    if source not in valid_sources:
        source = "google"
    
    result = await start_parsing.execute(
        db=db,
        keyword=request.keyword,
        depth=request.depth,
        source=source
    )
    await db.commit()
    
    # Return response with camelCase field names for frontend
    return JSONResponse(
        status_code=201,
        content={
            "runId": result["run_id"],
            "keyword": result["keyword"],
            "status": result["status"]
        }
    )
```

**3. Usecase запускает парсинг (с защитой от дублирования):**

```python
# backend/app/usecases/start_parsing.py
# Глобальный set для отслеживания активных задач
_running_parsing_tasks = set()

async def execute(db: AsyncSession, keyword: str, depth: int = 10, source: str = "google", background_tasks=None):
    # Create parsing request and run in database
    run_id = str(uuid.uuid4())
    # ...
    
    # Start parsing asynchronously
    async def run_parsing():
        # Дополнительная защита внутри функции
        if run_id in _running_parsing_tasks:
            if run_id in start_parsing_module._processing_tasks:
                logger.warning(f"[DUPLICATE DETECTED] Task {run_id} already processing, skipping")
                return
            start_parsing_module._processing_tasks.add(run_id)
        
        parser_client = ParserClient(settings.parser_service_url)
        result = await parser_client.parse(keyword=keyword, depth=depth, source=source)
        # Save results to domains_queue
        # Update run status to "completed"
    
    # ЗАЩИТА ОТ ДУБЛИРОВАНИЯ: Проверка ПЕРЕД добавлением в BackgroundTasks
    if background_tasks is not None:
        if run_id in _running_parsing_tasks:
            logger.warning(f"[DUPLICATE PREVENTION] run_id {run_id} already in running tasks, skipping")
            return result
        
        # Добавление ПЕРЕД background_tasks.add_task для предотвращения гонки условий
        _running_parsing_tasks.add(run_id)
        background_tasks.add_task(run_parsing)
    
    return {
        "run_id": run_id,
        "keyword": keyword,
        "status": "running"
    }
```

**4. Parser Client вызывает Parser Service:**

```python
# backend/app/adapters/parser_client.py
async def parse(self, keyword: str, depth: int = 10, source: str = "google") -> Dict[str, Any]:
    response = await self.client.post(
        "/parse",
        json={
            "keyword": keyword,
            "depth": depth,
            "source": source
        },
        headers={
            "Content-Type": "application/json; charset=utf-8"
        }
    )
    return response.json()
```

**5. Parser Service выполняет парсинг (с защитой от дублирования):**

```python
# parser_service/api.py
_running_parse_requests = set()
_parse_lock = asyncio.Lock()

@app.post("/parse", response_model=ParseResponse)
async def parse_keyword(request: ParseRequest):
    request_key = f"{request.keyword}_{request.depth}_{request.source}"
    
    # ЗАЩИТА ОТ ДУБЛИРОВАНИЯ: Проверка с блокировкой
    async with _parse_lock:
        if request_key in _running_parse_requests:
            logger.warning(f"[DUPLICATE DETECTED] Request '{request_key}' already running, skipping")
            return ParseResponse(keyword=request.keyword, suppliers=[], total_found=0)
        _running_parse_requests.add(request_key)
    
    try:
        # Connect to Chrome CDP
        # Open search engine pages (Google/Yandex)
        # Collect links from search results
        # Return suppliers list
        return ParseResponse(keyword=request.keyword, suppliers=suppliers, total_found=len(suppliers))
    finally:
        async with _parse_lock:
            _running_parse_requests.discard(request_key)
```

**Полный код схем и типов:**

**Backend схемы (Pydantic):**

```python
# backend/app/transport/schemas/parsing.py
class StartParsingRequestDTO(BaseModel):
    """Request DTO for starting parsing."""
    keyword: str
    depth: int = Field(default=10, description="Number of search result pages to parse (depth)")
    source: str = Field(default="google", description="Source for parsing: 'google', 'yandex', or 'both'")

class StartParsingResponseDTO(BaseModel):
    """Response DTO for parsing start."""
    runId: str  # Use camelCase directly (no alias needed for response)
    keyword: str
    status: str

class ParsingStatusResponseDTO(BaseModel):
    """Response DTO for parsing status."""
    runId: str = Field(alias="run_id")
    keyword: str
    status: str
    startedAt: Optional[datetime] = Field(None, alias="started_at")
    finishedAt: Optional[datetime] = Field(None, alias="finished_at")
    error: Optional[str] = Field(None, alias="error_message")
    resultsCount: Optional[int] = None
```

**Frontend типы (TypeScript):**

```typescript
// frontend/moderator-dashboard-ui/lib/types.ts
export interface ParsingRunDTO {
  run_id?: string  // Backend возвращает snake_case
  runId?: string  // Для обратной совместимости
  keyword: string
  status: string  // Может быть любым статусом, не только "running" | "completed" | "failed"
  started_at?: string | null  // Backend возвращает snake_case
  startedAt?: string | null  // Для обратной совместимости
  finished_at?: string | null  // Backend возвращает snake_case
  finishedAt?: string | null  // Для обратной совместимости
  error_message?: string | null  // Backend возвращает snake_case
  error?: string | null  // Для обратной совместимости
  resultsCount: number | null
  created_at?: string  // Backend возвращает snake_case
  createdAt?: string  // Для обратной совместимости
}

export interface DomainQueueEntryDTO {
  domain: string
  keyword: string
  url: string
  parsingRunId: string | null
  status: string
  createdAt: string
}
```

**Parser Service схемы:**

```python
# parser_service/api.py
class ParseRequest(BaseModel):
    """Request model for parsing."""
    keyword: str
    depth: int = 10  # Number of search result pages to parse
    source: str = "google"  # "google", "yandex", or "both"

class ParsedSupplier(BaseModel):
    """Parsed supplier data."""
    name: str
    domain: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    inn: Optional[str] = None
    source_url: str

class ParseResponse(BaseModel):
    """Response model for parsing."""
    keyword: str
    suppliers: List[ParsedSupplier]
    total_found: int
```

**Проверка работоспособности:**

```bash
# 1. Запустить все сервисы
start-all.bat

# 2. Проверить доступность сервисов
curl http://127.0.0.1:8000/health      # Backend
curl http://127.0.0.1:9003/health     # Parser Service
curl http://127.0.0.1:9222/json/version  # Chrome CDP

# 3. Запустить парсинг
curl -X POST http://127.0.0.1:8000/parsing/start \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"keyword":"кирпич","depth":1,"source":"google"}'

# 4. Проверить результаты
curl "http://127.0.0.1:8000/domains/queue?parsingRunId=<runId>"
```

**Ожидаемый результат:**
- В окне Chrome открываются вкладки с Google/Yandex поиском
- Парсинг выполняется реально (не мгновенно)
- Результаты сохраняются в базу данных
- Возвращается новый runId с новыми результатами

#### `GET /parsing/status/{run_id}`
Статус парсинга.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (с известной проблемой валидации - см. ниже)

**Path параметры:**
- `run_id` (string) - UUID запуска

**Response:** `ParsingStatusResponseDTO`

**Как работает:**

```python
# backend/app/transport/routers/parsing.py
@router.get("/status/{run_id}", response_model=ParsingStatusResponseDTO)
async def get_parsing_status_endpoint(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    run = await get_parsing_status.execute(db=db, run_id=run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Parsing run not found")
    
    # Extract keyword from request
    keyword = "Unknown"
    if run.request:
        if run.request.title:
            keyword = run.request.title
        elif run.request.raw_keys_json:
            # Parse JSON and extract first keyword
            keys_data = json.loads(run.request.raw_keys_json)
            # ...
    
    status_dict = {
        "runId": run.run_id,
        "keyword": keyword,
        "status": run.status,
        "startedAt": run.started_at.isoformat() if run.started_at else None,
        "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
        "error": run.error_message,
        "resultsCount": None,
    }
    return ParsingStatusResponseDTO.model_validate(status_dict)
```

**⚠️ Известная проблема:**
- Endpoint может возвращать ошибку валидации Pydantic: `Field required [type=missing, input_value={'runId': ...}, input_type=dict]`
- Проблема в маппинге `runId` vs `run_id` в DTO
- **Временное решение:** Использовать прямой запрос к базе или endpoint `/parsing-runs/{run_id}`

**Известные ограничения:**

**⚠️ ТРЕБУЕТ РАБОТЫ: CAPTCHA**

**Проблема:**
- При парсинге Google/Yandex может появляться CAPTCHA
- Парсер ожидает, что пользователь решит CAPTCHA вручную в видимом окне Chrome
- Если CAPTCHA не решена в течение 5 минут - парсинг может завершиться с ошибкой

**Текущее поведение:**
- Парсер обнаруживает CAPTCHA и ждет до 5 минут
- Выводит сообщения: `[WAIT] GOOGLE: Waiting for CAPTCHA to be solved...`
- Пользователь должен вручную решить CAPTCHA в окне Chrome
- После решения CAPTCHA парсинг продолжается автоматически

**Что нужно сделать в будущем:**
- [ ] Интеграция с сервисами решения CAPTCHA (2captcha, anti-captcha и т.д.)
- [ ] Автоматическое определение и решение CAPTCHA
- [ ] Улучшенная обработка CAPTCHA с уведомлениями пользователю
- [ ] Возможность пропускать страницы с CAPTCHA и продолжать парсинг

**Приоритет:** Средний (парсинг работает, но требует ручного вмешательства при CAPTCHA)

---

### Полный поток данных при парсинге

**1. Frontend → Backend (запуск парсинга):**

```
POST http://127.0.0.1:8000/parsing/start
Content-Type: application/json; charset=utf-8

{
  "keyword": "кирпич",
  "depth": 2,
  "source": "google"
}
```

**2. Backend создает запись в БД:**

```python
# Создается parsing_request
{
  "title": "кирпич",
  "raw_keys_json": "[\"кирпич\"]",
  "source": "google"
}

# Создается parsing_run
{
  "run_id": "4f468e53-9ec5-4c03-aebf-04c54bdf5477",
  "request_id": <request_id>,
  "status": "running",
  "source": "google",
  "depth": 2,
  "started_at": "2025-12-27T10:15:00Z"
}
```

**3. Backend → Parser Service (асинхронно):**

```
POST http://127.0.0.1:9003/parse
Content-Type: application/json; charset=utf-8

{
  "keyword": "кирпич",
  "depth": 2,
  "source": "google"
}
```

**4. Parser Service подключается к Chrome CDP:**

```python
# parser_service/src/parser.py
# 1. Подключение к Chrome CDP
browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")

# 2. Использование существующего контекста браузера
contexts = browser.contexts
context = contexts[0]  # Используем первый профиль

# 3. Создание новой вкладки для поисковика
page = await context.new_page()

# 4. Открытие поисковика
await page.goto("https://www.google.com/search?q=кирпич+купить&hl=ru")

# 5. Сбор ссылок с результатов поиска
# 6. Парсинг следующих страниц (depth раз)
```

**5. Parser Service → Backend (результаты):**

```
Response:
{
  "keyword": "кирпич",
  "suppliers": [
    {
      "name": "kirpich-lavka.ru",
      "domain": "kirpich-lavka.ru",
      "email": null,
      "phone": null,
      "inn": null,
      "source_url": "https://kirpich-lavka.ru/..."
    },
    ...
  ],
  "total_found": 119
}
```

**6. Backend сохраняет результаты в БД:**

```python
# Для каждого supplier создается запись в domains_queue
{
  "domain": "kirpich-lavka.ru",
  "keyword": "кирпич",
  "url": "https://kirpich-lavka.ru/...",
  "parsing_run_id": "4f468e53-9ec5-4c03-aebf-04c54bdf5477",
  "status": "pending"
}
```

**7. Backend обновляет статус парсинга:**

```python
# Обновление parsing_run
{
  "status": "completed",
  "finished_at": "2025-12-27T10:20:00Z",
  "results_count": 119
}
```

**8. Frontend получает результаты:**

```
GET http://127.0.0.1:8000/domains/queue?parsingRunId=4f468e53-9ec5-4c03-aebf-04c54bdf5477

Response:
{
  "entries": [
    {
      "domain": "kirpich-lavka.ru",
      "keyword": "кирпич",
      "url": "https://kirpich-lavka.ru/...",
      "parsingRunId": "4f468e53-9ec5-4c03-aebf-04c54bdf5477",
      "status": "pending",
      "createdAt": "2025-12-27T10:20:00Z"
    },
    ...
  ],
  "total": 119,
  "limit": 100,
  "offset": 0
}
```

---

### Проверка работоспособности всей связки

**Команды для проверки:**

```bash
# 1. Проверить все сервисы
curl http://127.0.0.1:8000/health      # Backend
curl http://127.0.0.1:9003/health     # Parser Service
curl http://127.0.0.1:9222/json/version  # Chrome CDP

# 2. Запустить парсинг
curl -X POST http://127.0.0.1:8000/parsing/start \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"keyword":"кирпич","depth":1,"source":"google"}'

# Ответ:
# {
#   "runId": "4f468e53-9ec5-4c03-aebf-04c54bdf5477",
#   "keyword": "кирпич",
#   "status": "running"
# }

# 3. Проверить статус (подождать 10-30 секунд)
curl "http://127.0.0.1:8000/parsing/status/4f468e53-9ec5-4c03-aebf-04c54bdf5477"

# 4. Проверить результаты
curl "http://127.0.0.1:8000/domains/queue?parsingRunId=4f468e53-9ec5-4c03-aebf-04c54bdf5477&limit=10"

# 5. Проверить вкладки Chrome (должны быть открыты вкладки с поисковиками)
curl http://127.0.0.1:9222/json | python -m json.tool | grep -i "google\|yandex"
```

**Ожидаемое поведение:**

1. ✅ Backend возвращает runId немедленно
2. ✅ В окне Chrome открываются вкладки с Google/Yandex поиском
3. ✅ Парсинг выполняется реально (занимает время, не мгновенно)
4. ✅ Результаты сохраняются в базу данных
5. ✅ Статус парсинга обновляется на "completed"
6. ✅ Результаты доступны через `/domains/queue?parsingRunId=...`

**Что проверить визуально:**

- Откройте окно Chrome (должно быть запущено с CDP)
- Следите за вкладками - должны открываться вкладки с поисковиками
- В истории браузера должны появиться записи о посещении Google/Yandex
- После завершения парсинга вкладки могут закрыться автоматически

### 2.6 Parsing Runs (История парсинга)

**Базовый путь:** `/parsing/runs`

#### `GET /parsing/runs`
Список запусков парсинга.

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)

**Response:** `ParsingRunsListResponseDTO`

#### `GET /parsing/runs/{run_id}`
Получить запуск по ID.

**Path параметры:**
- `run_id` (string) - UUID запуска

**Response:** `ParsingRunDTO`

**Ошибки:**
- `404` - запуск не найден

#### `DELETE /parsing/runs/{run_id}`
Удалить один запуск парсинга.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-28)

**Path параметры:**
- `run_id` (string) - UUID запуска

**Response:** `204 No Content` (пустое тело)

**Ошибки:**
- `404` - запуск не найден
- `500` - ошибка при удалении

**Как работает:**
1. Frontend вызывает `DELETE /parsing/runs/{run_id}` через `apiFetch`
2. Backend выполняет прямой SQL `DELETE FROM parsing_runs WHERE run_id = :run_id`
3. Backend делает `commit()` транзакции
4. Backend возвращает `204 No Content`
5. Frontend обновляет список через `loadRuns()` с текущими параметрами URL

**Проверка работоспособности:**
```powershell
# 1. Получить список runs
curl "http://127.0.0.1:8000/parsing/runs?limit=5&offset=0"

# 2. Удалить один run
curl -X DELETE "http://127.0.0.1:8000/parsing/runs/{run_id}"

# 3. Проверить, что run удален
curl "http://127.0.0.1:8000/parsing/runs?limit=10&offset=0"
# Удаленный run не должен присутствовать в списке
```

**Ожидаемый результат:**
- Endpoint возвращает `204 No Content`
- Запись удаляется из базы данных
- Frontend обновляется и не показывает удаленную запись

#### `GET /parsing/runs/{run_id}/logs`
Получить логи парсинга для запуска.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Path параметры:**
- `run_id` (string) - UUID запуска

**Response:**
```json
{
  "run_id": "uuid",
  "parsing_logs": {
    "google": {
      "total_links": 8,
      "pages_processed": 1,
      "links_by_page": {"1": 16},
      "last_links": ["https://example.com/page1", ...]
    },
    "yandex": {
      "total_links": 10,
      "pages_processed": 1,
      "links_by_page": {"1": 20},
      "last_links": ["https://example.com/page2", ...]
    }
  }
}
```

**Ошибки:**
- Если run не найден, возвращается пустой объект `{"run_id": "...", "parsing_logs": {}}` (не 404)

**Как работает:**
1. Frontend вызывает `GET /parsing/runs/{run_id}/logs` через `getParsingLogs()`
2. Backend извлекает `parsing_logs` из `process_log["parsing_logs"]` в таблице `parsing_runs`
3. Backend возвращает логи или пустой объект, если логов нет

**Проверка работоспособности:**
```powershell
# Получить логи парсинга
$runId = "<run_id>"
curl "http://127.0.0.1:8000/parsing/runs/$runId/logs"
```

**Ожидаемый результат:**
- Endpoint возвращает `parsing_logs` с информацией о найденных ссылках для Google и Yandex
- `last_links` содержит последние 20 найденных ссылок для каждого поисковика

#### `PUT /parsing/runs/{run_id}/logs`
Обновить логи парсинга для запуска (используется Parser Service).

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Path параметры:**
- `run_id` (string) - UUID запуска

**Request body:**
```json
{
  "parsing_logs": {
    "google": {
      "total_links": 8,
      "pages_processed": 1,
      "links_by_page": {"1": 16},
      "last_links": ["https://example.com/page1", ...]
    },
    "yandex": {
      "total_links": 10,
      "pages_processed": 1,
      "links_by_page": {"1": 20},
      "last_links": ["https://example.com/page2", ...]
    }
  }
}
```

**Response:** `200 OK` с обновленными логами

**Как работает:**
1. Parser Service отправляет обновленные `parsing_logs` каждые 2.5 секунды
2. Backend обновляет `process_log["parsing_logs"]` в таблице `parsing_runs`
3. Frontend может получить обновленные логи через `GET /parsing/runs/{run_id}/logs`

#### Определение источников для доменов (Google/Яндекс) ✅ Проверено и работает

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Описание рабочей связки Backend-Frontend:**

Определение и отображение источников (Google/Яндекс) для доменов на основе `parsing_logs`. Бейджи показывают, какой поисковик реально нашел URL для каждого домена.

**⚠️ КРИТИЧЕСКИ ВАЖНО:** Используется `parsing_logs` для определения источников, а не `source` из БД, так как в БД все URL имеют `source="both"` когда оба поисковика работают.

**📚 Подробная документация:** [`docs/SOURCE_DETERMINATION_FLOW.md`](SOURCE_DETERMINATION_FLOW.md)

**Endpoint'ы и функции:**

1. **Backend:**
   - `GET /parsing/runs/{run_id}/logs` - получение `parsing_logs`
   - `PUT /parsing/runs/{run_id}/logs` - обновление `parsing_logs` (Parser Service)

2. **Frontend:**
   - `getParsingLogs(runId)` в `lib/api.ts` - получение логов
   - `collectDomainSources(urls, parsingLogs)` в `lib/utils-domain.ts` - определение источников
   - Отображение бейджей в `app/parsing-runs/[runId]/page.tsx`

**Команды для проверки работоспособности:**

```powershell
# 1. Получить parsing_logs
$runId = "<run_id>"
$logs = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/runs/$runId/logs"
Write-Host "Google: $($logs.parsing_logs.google.total_links) links"
Write-Host "Yandex: $($logs.parsing_logs.yandex.total_links) links"

# 2. Проверить источники URL в БД
$domains = Invoke-RestMethod -Uri "http://127.0.0.1:8000/domains/queue?parsingRunId=$runId&limit=1000"
Write-Host "Total URLs: $($domains.entries.Count)"
Write-Host "Google: $(($domains.entries | Where-Object { $_.source -eq 'google' }).Count)"
Write-Host "Yandex: $(($domains.entries | Where-Object { $_.source -eq 'yandex' }).Count)"
Write-Host "Both: $(($domains.entries | Where-Object { $_.source -eq 'both' }).Count)"

# 3. Проверить на фронтенде
# Открыть: http://localhost:3000/parsing-runs/$runId
# Проверить, что бейджи Google/Яндекс отображаются корректно для каждого домена
```

**Ожидаемый результат:**

- Домены показывают только те бейджи (Google/Яндекс), которые реально нашли их URL согласно `parsing_logs`
- Если URL найден только Google - показывается только синий бейдж "Google"
- Если URL найден только Яндекс - показывается только желтый бейдж "Яндекс"
- Если URL найден обоими - показываются оба бейджа

**Примеры запросов/ответов:**

**Запрос:**
```powershell
curl "http://127.0.0.1:8000/parsing/runs/1140b974-e97b-47fb-a26c-94e956ac7fd5/logs"
```

**Ответ:**
```json
{
  "run_id": "1140b974-e97b-47fb-a26c-94e956ac7fd5",
  "parsing_logs": {
    "google": {
      "total_links": 8,
      "pages_processed": 1,
      "links_by_page": {"1": 16},
      "last_links": [
        "https://metallobazav.ru/catalog/armatura/",
        "https://petrovich.ru/catalog/12107/",
        ...
      ]
    },
    "yandex": {
      "total_links": 10,
      "pages_processed": 1,
      "links_by_page": {"1": 20},
      "last_links": [
        "https://MetallobazaV.ru/catalog/armatura/",
        "https://Petrovich.ru/catalog/12107/",
        ...
      ]
    }
  }
}
```

**Логика работы:**

1. **Parser Service** собирает URL и определяет источники, обновляет `parsing_logs`
2. **Backend** сохраняет `parsing_logs` в `process_log["parsing_logs"]` в таблице `parsing_runs`
3. **Frontend** загружает `parsing_logs` вместе с данными из `domains_queue`
4. **Frontend** использует `collectDomainSources(group.urls, parsingLogs)` для определения источников
5. **Frontend** отображает бейджи на основе определенных источников

**Код Frontend:**

```typescript
// Загрузка данных
const [runData, domainsData, logsData] = await Promise.all([
  getParsingRun(runId),
  getDomainsQueue({ parsingRunId: runId, limit: 1000 }),
  getParsingLogs(runId).catch(() => ({ parsing_logs: {} }))
])

// Определение источников
const parsingLogsForSources = logsData.parsing_logs && Object.keys(logsData.parsing_logs).length > 0 
  ? logsData.parsing_logs 
  : null

const sources = collectDomainSources(group.urls, parsingLogsForSources)

// Отображение бейджей
{group.sources && group.sources.includes("google") && (
  <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300 text-xs">
    Google
  </Badge>
)}
{group.sources && group.sources.includes("yandex") && (
  <Badge variant="outline" className="bg-yellow-100 text-yellow-700 border-yellow-300 text-xs">
    Яндекс
  </Badge>
)}
```

#### `DELETE /parsing/runs/bulk`
Массовое удаление запусков парсинга.

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-28)

**Request body:**
```json
["run-id-1", "run-id-2", "run-id-3"]
```
или
```json
{
  "run_ids": ["run-id-1", "run-id-2", "run-id-3"]
}
```

**Response:**
- **200 OK** (если все удалены успешно):
  ```json
  {
    "deleted": 3,
    "total": 3
  }
  ```
- **207 Multi-Status** (если есть ошибки):
  ```json
  {
    "deleted": 2,
    "total": 3,
    "errors": ["Error deleting run-id-3: ..."]
  }
  ```

**Ошибки:**
- `400` - неверный формат body (не список или пустой список)

**Как работает:**
1. Frontend собирает `runIds` из выделенных записей
2. Frontend вызывает `DELETE /parsing/runs/bulk` с массивом `runIds` через `apiFetch`
3. Backend для каждого `run_id`:
   - Создает отдельную сессию БД
   - Выполняет прямой SQL `DELETE FROM parsing_runs WHERE run_id = :run_id`
   - Делает `commit()` в отдельной сессии
   - Логирует в audit_log ПОСЛЕ commit (в отдельной сессии)
4. Backend возвращает `200` или `207` с результатами
5. Frontend обновляет список через `loadRuns()` с текущими параметрами URL
6. Frontend обновляет пагинацию, если текущая страница стала пустой

**Критически важные детали реализации:**
- **Отдельные сессии для каждого удаления** - предотвращает `InFailedSQLTransactionError`
- **Audit log ПОСЛЕ commit** - ошибки аудита не откатывают удаление
- **Проверка удаления через новую сессию** - чтение из БД, а не из кэша сессии
- **Порядок маршрутов** - `/runs/bulk` ДО `/runs/{run_id}` в FastAPI router

**Проверка работоспособности:**
```powershell
# 1. Получить список runs со статусом "failed"
curl "http://127.0.0.1:8000/parsing/runs?status=failed&limit=5&offset=0"

# 2. Удалить несколько runs
curl -X DELETE "http://127.0.0.1:8000/parsing/runs/bulk" \
  -H "Content-Type: application/json" \
  -d '["run-id-1", "run-id-2", "run-id-3"]'

# 3. Проверить, что runs удалены
curl "http://127.0.0.1:8000/parsing/runs?status=failed&limit=10&offset=0"
# Удаленные runs не должны присутствовать в списке
```

**Проверка через Frontend:**
1. Открыть `http://localhost:3000/parsing-runs`
2. Выбрать статус "Ошибка" в Select - список должен обновиться
3. Выделить все записи со статусом "Ошибка" (или несколько записей)
4. Нажать кнопку "Удалить"
5. Убедиться, что:
   - Записи удалены из списка
   - Список обновился автоматически
   - Пагинация скорректирована, если текущая страница стала пустой
   - В консоли браузера нет ошибок

**Ожидаемый результат:**
- Endpoint возвращает `200` или `207` с корректным `deleted` count
- Все записи удаляются из базы данных
- Frontend обновляется и не показывает удаленные записи
- Select статуса работает корректно (сразу обновляет URL)
- В логах Backend видны сообщения "Committed deletion" и "Verified: Run ... deleted successfully"

### 2.7 Blacklist (Черный список)

**Базовый путь:** `/moderator/blacklist`

#### `GET /moderator/blacklist`
Список записей черного списка.

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)

**Response:** `BlacklistResponseDTO`

#### `POST /moderator/blacklist`
Добавить домен в черный список.

**Request body:** `AddToBlacklistRequestDTO` (camelCase)

**Особенности:**
- Backend конвертирует `addedBy` → `added_by`, `parsingRunId` → `parsing_run_id`

**Response:** `BlacklistEntryDTO` (status 201)

#### `DELETE /moderator/blacklist/{domain}`
Удалить домен из черного списка.

**Path параметры:**
- `domain` (string) - домен

**Response:** `204 No Content`

**Ошибки:**
- `404` - домен не найден в черном списке

### 2.8 Health Check

#### `GET /health`
Проверка работоспособности.

**Статус:** ✅ **ПРОВЕРЕНО** (базовый endpoint, должен работать)

**Response:**
```json
{
  "status": "ok"
}
```

---

## 3. Frontend (Next.js)

### 3.1 Технологии

- **Next.js 16** (App Router)
- **TypeScript** (strict mode)
- **React 18**
- **Tailwind CSS**
- **Shadcn UI**

### 3.2 Структура страниц

**Статус проверки:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ** (исправлены ошибки с params и NaN, но требует проверки на реальных данных)

#### `/` (Главная - Dashboard)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Функциональность:**
- ✅ Форма запуска нового парсинга (ключевое слово, глубина, источник)
- ✅ Метрики: В очереди, Новые поставщики, Активных парсингов, Blacklist
- ✅ Последние запуски (горизонтальный скролл)
- ✅ Прогрессбар при запуске парсинга с polling статуса
- ✅ CTA кнопки: Обработать очередь, Проверить новых, Управление Blacklist

**Связка Backend-Frontend:**

**1. Загрузка метрик:**
```typescript
// frontend/moderator-dashboard-ui/app/page.tsx
const [domainsData, suppliersData, runsData, blacklistData] = await Promise.all([
  getDomainsQueue({ limit: 1 }),              // GET /domains/queue?limit=1
  getSuppliers({ limit: 1 }),                  // GET /moderator/suppliers?limit=1
  getParsingRuns({ status: "running", limit: 1 }),  // GET /parsing/runs?status=running&limit=1
  getBlacklist({ limit: 1 }),                  // GET /moderator/blacklist?limit=1
])

const recentRunsData = await getParsingRuns({ 
  limit: 10, 
  sort: "created_at", 
  order: "desc" 
})  // GET /parsing/runs?limit=10&sort=created_at&order=desc
```

**2. Запуск парсинга:**
```typescript
// При нажатии "Запустить парсинг"
const result = await startParsing({
  keyword: keyword.trim(),
  depth,
  source,
})  // POST /parsing/start

// Устанавливаем прогрессбар
setParsingProgress({ isRunning: true, runId: result.runId, status: "running" })
// Пользователь остается на главной странице (не переходит автоматически)
```

**3. Polling статуса парсинга:**
```typescript
// Polling каждые 3 секунды для обновления статуса
useEffect(() => {
  if (!parsingProgress.isRunning || !parsingProgress.runId) return

  const interval = setInterval(async () => {
    const run = await getParsingRun(parsingProgress.runId!)  // GET /parsing/runs/{runId}
    if (run.status === "completed" || run.status === "failed") {
      setParsingProgress({ isRunning: false, runId: null, status: run.status })
      loadDashboardData()
      toast.success("Парсинг завершен")
    } else {
      setParsingProgress((prev) => ({ ...prev, status: run.status }))
    }
  }, 3000)

  return () => clearInterval(interval)
}, [parsingProgress.isRunning, parsingProgress.runId])
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000`
2. Проверить, что метрики загружаются и отображаются
3. Проверить, что последние запуски отображаются
4. Запустить парсинг - должен появиться прогрессбар
5. Проверить, что прогрессбар обновляется каждые 3 секунды
6. Проверить, что после завершения парсинга прогрессбар скрывается
7. Проверить, что пользователь остается на главной странице (не переходит автоматически)

**Ожидаемый результат:**
- Метрики отображаются корректно
- Последние запуски отображаются в горизонтальном скролле
- Прогрессбар появляется при запуске парсинга
- Статус парсинга обновляется через polling
- Пользователь остается на главной странице

#### `/suppliers` (Список поставщиков)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-30)

**Функциональность:**
- ✅ Список всех поставщиков с пагинацией
- ✅ Фильтрация по типу (supplier/reseller)
- ✅ Выбор нескольких поставщиков (чекбоксы)
- ✅ Массовое удаление поставщиков
- ✅ Отображение основных данных (название, ИНН, домен, тип)

**Связка Backend-Frontend:**

**1. Загрузка списка поставщиков:**
```typescript
// frontend/moderator-dashboard-ui/app/suppliers/suppliers-client.tsx
const suppliersData = await getSuppliers({ limit: 1000 })  // GET /moderator/suppliers?limit=1000
```

**2. Массовое удаление:**
```typescript
// При нажатии "Удалить выбранные"
for (const id of selectedIds) {
  await deleteSupplier(id)  // DELETE /moderator/suppliers/{id}
}
// После удаления список перезагружается
loadData()
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/suppliers`
2. Проверить, что список поставщиков загружается и отображается
3. Выделить несколько поставщиков (чекбоксы)
4. Нажать "Удалить выбранные" - поставщики должны исчезнуть
5. Проверить консоль браузера (F12) - не должно быть ошибок

**Ожидаемый результат:**
- Список поставщиков отображается корректно
- Чекбоксы работают для выбора нескольких поставщиков
- Массовое удаление работает
- Список обновляется после удаления

#### `/suppliers/[id]` (Детали поставщика)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-30)

**Функциональность:**
- ✅ Отображение полной информации о поставщике
- ✅ Карточка поставщика с Checko данными:
  - Финансовый профиль (графики выручки и прибыли, история по годам)
  - Оценка надежности (с категориями: положительные, требуют внимания, негативные)
  - ОКВЭД (в одной гармошке)
  - Риски (арбитраж, проверки, исполнительные производства)
  - Учредители и руководители (с ссылками на Checko.ru)
- ✅ Действия: Редактировать, Загрузить данные Checko, Blacklist, Ключевые слова
- ✅ Отображение всех Checko данных (финансы, юридические дела, проверки)

**Связка Backend-Frontend:**

**1. Загрузка данных поставщика:**
```typescript
// frontend/moderator-dashboard-ui/app/suppliers/[id]/supplier-detail-client.tsx
const supplier = await getSupplier(supplierId)  // GET /moderator/suppliers/{id}
// checkoData извлекается из supplier.checkoData (JSON строка)
const checkoData = supplier.checkoData ? JSON.parse(supplier.checkoData) : null
```

**2. Загрузка данных Checko:**
```typescript
// При нажатии "Загрузить данные Checko"
const checkoResponse = await getCheckoData(supplier.inn, false)  // GET /moderator/checko/{inn}
// Обновление поставщика с данными Checko
const updatedSupplier = await updateSupplier(supplier.id, {
  // ... все Checko поля
  checkoData: checkoResponse.checkoData || null,
})  // PUT /moderator/suppliers/{id}
```

**3. Отображение данных:**
```typescript
// frontend/moderator-dashboard-ui/components/supplier-card.tsx
// Используется компонент SupplierCard для отображения всех данных
// - Финансовые графики (recharts)
// - Оценка надежности (calculateReliabilityScore)
// - ОКВЭД (accordion)
// - Риски (с вердиктом и рекомендациями)
// - Учредители и руководители (с ссылками)
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/suppliers/{id}`
2. Проверить, что карточка поставщика отображается
3. Проверить, что финансовые графики отображаются (если есть данные)
4. Проверить, что оценка надежности отображается с категориями
5. Проверить, что ОКВЭД отображаются в гармошке
6. Проверить, что учредители отображаются с ссылками на Checko.ru
7. Нажать "Загрузить данные Checko" - данные должны обновиться
8. Проверить консоль браузера (F12) - не должно быть ошибок

**Ожидаемый результат:**
- Карточка поставщика отображается корректно
- Все Checko данные отображаются (финансы, риски, учредители)
- Финансовые графики работают (recharts)
- Оценка надежности рассчитывается и отображается с категориями
- ОКВЭД отображаются в одной гармошке
- Учредители имеют ссылки на Checko.ru (если есть ИНН)

#### `/suppliers/[id]/edit` (Редактирование поставщика)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-30)

**Функциональность:**
- ✅ Форма редактирования/создания поставщика
- ✅ Поля: name, inn, email, domain, address, type
- ✅ Кнопка "Заполнить Данные" для загрузки данных из Checko
- ✅ Автоматическое заполнение полей из Checko API
- ✅ Сохранение всех Checko данных (включая checkoData)

**Связка Backend-Frontend:**

**1. Загрузка данных поставщика (при редактировании):**
```typescript
// frontend/moderator-dashboard-ui/app/suppliers/[id]/edit/supplier-edit-client.tsx
const supplier = await getSupplier(supplierId)  // GET /moderator/suppliers/{id}
// Заполнение формы всеми полями, включая Checko поля
setFormData({
  name: supplier.name,
  inn: supplier.inn,
  // ... все Checko поля
  checkoData: supplier.checkoData || null,
})
```

**2. Загрузка данных из Checko:**
```typescript
// При нажатии "Заполнить Данные"
const checkoResponse = await getCheckoData(formData.inn, false)  // GET /moderator/checko/{inn}
// Автоматическое заполнение формы
setFormData({
  ...formData,
  name: checkoResponse.name || formData.name,
  ogrn: checkoResponse.ogrn || null,
  kpp: checkoResponse.kpp || null,
  // ... все Checko поля
  checkoData: checkoResponse.checkoData || null,
})
```

**3. Сохранение поставщика:**
```typescript
// При нажатии "Сохранить"
if (supplierId) {
  await updateSupplier(supplierId, formData)  // PUT /moderator/suppliers/{id}
} else {
  await createSupplier(formData)  // POST /moderator/suppliers
}
// Все Checko поля отправляются в camelCase
// Backend конвертирует camelCase → snake_case для БД
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/suppliers/{id}/edit`
2. Проверить, что форма загружается с данными поставщика
3. Ввести ИНН и нажать "Заполнить Данные"
4. Проверить, что поля автоматически заполняются данными из Checko
5. Сохранить изменения - поставщик должен обновиться
6. Проверить консоль браузера (F12) - не должно быть ошибок

**Ожидаемый результат:**
- Форма редактирования работает корректно
- Кнопка "Заполнить Данные" загружает данные из Checko
- Все Checko поля сохраняются в БД
- Данные отображаются корректно после сохранения

#### `/keywords` (Ключевые слова)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Функциональность:**
- ✅ Двойной Accordion: ключи → домены → URL
- ✅ Группировка поддоменов под основным доменом (krn.specstali.ru, spb.specstali.ru → specstali.ru)
- ✅ Отображение статусов: Поставщик (зеленый), Реселлер (фиолетовый), Blacklist (красный)
- ✅ Добавление нового ключа
- ✅ Удаление ключа
- ✅ Автоматическое обновление списка

**Связка Backend-Frontend:**

**1. Загрузка данных:**
```typescript
// frontend/moderator-dashboard-ui/app/keywords/page.tsx
const [keywordsData, suppliersData, blacklistData] = await Promise.all([
  getKeywords(),                    // GET /keywords
  getSuppliers({ limit: 1000 }),    // GET /moderator/suppliers
  getBlacklist({ limit: 1000 }),    // GET /moderator/blacklist
])

// Для каждого ключа загружаем URL
const domainsData = await getDomainsQueue({ 
  keyword: keyword.keyword, 
  limit: 1000 
})  // GET /domains/queue?keyword={keyword}
```

**2. Группировка по доменам:**
```typescript
// Группируем URL по root domain с использованием extractRootDomain
const domainGroupsMap = new Map<string, DomainGroup>()
domainsData.entries.forEach((urlEntry) => {
  const rootDomain = extractRootDomain(urlEntry.domain).toLowerCase()
  // Поддомены (krn.specstali.ru, spb.specstali.ru) группируются под specstali.ru
  if (!domainGroupsMap.has(rootDomain)) {
    domainGroupsMap.set(rootDomain, {
      rootDomain,
      urls: [],
      supplierType: suppliersMap.get(rootDomain) || null,
      isBlacklisted: blacklistedDomains.has(rootDomain),
    })
  }
  domainGroupsMap.get(rootDomain)!.urls.push(urlEntry)
})
```

**3. Отображение статусов:**
- Поставщик: проверяется через `suppliersMap.get(rootDomain) === "supplier"`
- Реселлер: проверяется через `suppliersMap.get(rootDomain) === "reseller"`
- Blacklist: проверяется через `blacklistedDomains.has(rootDomain)`

**4. Автоматическое создание ключей при парсинге:**
```python
# backend/app/usecases/start_parsing.py
# После создания parsing run автоматически создается keyword
await create_keyword.execute(db=db, keyword=keyword)
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/keywords`
2. Проверить, что ключи отображаются в accordion
3. Раскрыть ключ - должны отображаться домены
4. Раскрыть домен - должны отображаться URL
5. Проверить, что поддомены группируются под основным доменом
6. Проверить, что статусы (Поставщик/Реселлер/Blacklist) отображаются корректно
7. Добавить новый ключ - должен появиться в списке
8. Запустить парсинг с новым ключом - ключ должен автоматически появиться в списке

**Ожидаемый результат:**
- Ключи отображаются в гармошке
- Домены группируются правильно (поддомены под основным)
- Статусы отображаются корректно
- Новые ключи создаются автоматически при парсинге

#### `/blacklist` (Черный список)
- Список доменов в черном списке
- Добавление домена
- Удаление домена
- **Статус:** ⚠️ **ТРЕБУЕТ ПРОВЕРКИ**

#### `/parsing-runs` (История парсинга)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-28)

**Функциональность:**
- ✅ Отображение списка parsing runs с пагинацией
- ✅ Фильтрация по статусу (все, выполняется, завершен, ошибка)
- ✅ Поиск по ключевому слову
- ✅ Сортировка (по дате создания, статусу)
- ✅ Удаление одной записи
- ✅ Массовое удаление записей
- ✅ Обновление списка после удаления
- ✅ Корректировка пагинации при удалении всех записей на странице

**Связка Backend-Frontend для удаления:**

**Single Delete:**
1. Пользователь нажимает кнопку удаления для одной записи
2. Frontend вызывает `DELETE /parsing/runs/{run_id}` через `apiFetch`
3. Backend удаляет запись и возвращает `204 No Content`
4. Frontend обновляет список через `loadRuns()` с текущими параметрами URL
5. Frontend корректирует пагинацию, если текущая страница стала пустой

**Bulk Delete:**
1. Пользователь выделяет несколько записей (чекбоксы)
2. Пользователь нажимает кнопку "Удалить"
3. Frontend собирает `runIds` из выделенных записей
4. Frontend вызывает `DELETE /parsing/runs/bulk` с массивом `runIds` через `apiFetch`
5. Backend удаляет все записи (каждая в отдельной сессии) и возвращает `200` или `207`
6. Frontend обновляет список через `loadRuns()` с текущими параметрами URL
7. Frontend корректирует пагинацию, если текущая страница стала пустой

**Фильтрация по статусу:**
1. Пользователь выбирает статус в Select компоненте
2. Frontend сразу обновляет URL через `router.push()` с новым параметром `status`
3. `useEffect` реагирует на изменение `searchParams` и вызывает `loadRuns()`
4. Backend возвращает отфильтрованный список
5. Frontend обновляет таблицу с новыми данными

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/parsing-runs`
2. Проверить, что список загружается и отображается
3. Выбрать статус "Ошибка" в Select - список должен обновиться
4. Выделить одну запись и удалить - запись должна исчезнуть
5. Выделить несколько записей и удалить - записи должны исчезнуть
6. Проверить, что пагинация работает корректно
7. Проверить консоль браузера (F12) - не должно быть ошибок

**Ожидаемый результат:**
- Список parsing runs отображается корректно
- Фильтрация по статусу работает (Select сразу обновляет URL)
- Удаление одной записи работает
- Массовое удаление работает
- Список обновляется после удаления
- Пагинация корректируется при удалении всех записей на странице
- В консоли браузера нет ошибок

#### `/parsing-runs/[runId]` (Детали запуска парсинга)

**Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-29)

**Функциональность:**
- ✅ Отображение деталей запуска (ключевое слово, статус, даты, глубина)
- ✅ Accordion с результатами парсинга, сгруппированными по доменам
- ✅ Фильтрация доменов из blacklist (домены в blacklist не отображаются)
- ✅ Отображение статусов доменов: Поставщик (зеленый), Реселлер (фиолетовый)
- ✅ Действия: Добавить в Blacklist, Создать поставщика, Создать реселлера
- ✅ Правильное форматирование дат (UTC)
- ✅ Отображение глубины парсинга

**Связка Backend-Frontend:**

**1. Загрузка данных:**
```typescript
// frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx
const [runData, domainsData, blacklistData, suppliersData] = await Promise.all([
  getParsingRun(runId),                                    // GET /parsing/runs/{runId}
  getDomainsQueue({ parsingRunId: runId, limit: 1000 }),   // GET /domains/queue?parsingRunId={runId}
  getBlacklist({ limit: 1000 }),                          // GET /moderator/blacklist
  getSuppliers({ limit: 1000 }),                          // GET /moderator/suppliers
])
```

**2. Фильтрация blacklist:**
```typescript
// Нормализуем домены для сравнения (lowercase + extractRootDomain)
const blacklistedDomains = new Set(
  blacklistData.entries.map((e) => extractRootDomain(e.domain).toLowerCase())
)
const filtered = domainsData.entries.filter((entry) => {
  const rootDomain = extractRootDomain(entry.domain).toLowerCase()
  return !blacklistedDomains.has(rootDomain)
})
```

**3. Определение статусов доменов:**
```typescript
// Создаем Map для быстрого поиска поставщиков по домену
const suppliersMap = new Map<string, "supplier" | "reseller">()
suppliersData.suppliers.forEach((supplier) => {
  if (supplier.domain) {
    const rootDomain = extractRootDomain(supplier.domain).toLowerCase()
    suppliersMap.set(rootDomain, supplier.type)
  }
})

// При группировке добавляем supplierType
const grouped = groupByDomain(filtered).map((group) => ({
  ...group,
  supplierType: suppliersMap.get(group.domain) || null,
}))
```

**4. Добавление в Blacklist:**
```typescript
// При нажатии "Добавить в Blacklist"
await addToBlacklist({ 
  domain: domain, 
  parsingRunId: runId || undefined 
})  // POST /moderator/blacklist
// После добавления данные перезагружаются, домен исчезает из результатов
loadData()
```

**5. Создание поставщика/реселлера:**
```typescript
// При нажатии "Создать поставщика" или "Создать реселлера"
await createSupplier({
  name: supplierForm.name,
  inn: supplierForm.inn || null,
  email: supplierForm.email || null,
  domain: supplierForm.domain || null,
  address: supplierForm.address || null,
  type: supplierForm.type,  // "supplier" или "reseller"
})  // POST /moderator/suppliers
// После создания данные перезагружаются, домен получает статус
loadData()
```

**6. Форматирование дат:**
```typescript
// Используется функция formatDate с UTC для правильного отображения
const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return "—"
  const date = new Date(dateString)
  return date.toLocaleString("ru-RU", {
    timeZone: "UTC",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}
```

**Проверка работоспособности:**
1. Открыть `http://localhost:3000/parsing-runs/{runId}`
2. Проверить, что детали запуска отображаются (ключевое слово, статус, даты, глубина)
3. Проверить, что результаты отображаются в accordion по доменам
4. Добавить домен в blacklist - домен должен исчезнуть из результатов
5. Создать поставщика из домена - домен должен получить зеленый бейдж "Поставщик"
6. Создать реселлера из домена - домен должен получить фиолетовый бейдж "Реселлер"
7. Проверить, что даты отображаются корректно (создан раньше завершен)

**Ожидаемый результат:**
- Детали запуска отображаются корректно
- Результаты группируются по доменам в accordion
- Домены из blacklist не отображаются
- Статусы доменов (Поставщик/Реселлер) отображаются корректно
- Действия работают и обновляют данные

#### `/manual-parsing` (Ручной парсинг)
- Форма запуска парсинга
- Поля: keyword, depth, source
- **Статус:** ✅ **ПРОВЕРЕНО И РАБОТАЕТ** (2025-12-27)

**Полный код компонента:**

```typescript
// frontend/moderator-dashboard-ui/app/manual-parsing/page.tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function ManualParsingPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState("")
  const [depth, setDepth] = useState(10)
  const [source, setSource] = useState<"google" | "yandex" | "both">("google")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleStart() {
    if (!keyword.trim()) {
      setError("Введите ключевое слово")
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await apiFetch<{ runId: string; keyword: string; status: string }>("/parsing/start", {
        method: "POST",
        body: JSON.stringify({ keyword, depth, source }),
      })
      router.push(`/parsing-runs/${data.runId}`)
    } catch (err) {
      console.error("[Manual Parsing] Error starting parsing:", {
        error: err,
        keyword: keyword,
        depth: depth,
        source: source,
        details: err instanceof APIError ? {
          status: err.status,
          message: err.message,
          data: err.data
        } : err
      })
      
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка запуска парсинга")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ручной парсинг</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500">{error}</div>}
        
        <div>
          <Label htmlFor="keyword">Ключевое слово</Label>
          <Input
            id="keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Например: металлопрокат"
            disabled={loading}
          />
        </div>

        <div>
          <Label htmlFor="source">Источник поиска</Label>
          <Select
            value={source}
            onValueChange={(value: "google" | "yandex" | "both") => setSource(value)}
            disabled={loading}
          >
            <SelectTrigger id="source">
              <SelectValue placeholder="Выберите источник" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="google">Google</SelectItem>
              <SelectItem value="yandex">Yandex</SelectItem>
              <SelectItem value="both">Google + Yandex</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="depth">Глубина парсинга (количество страниц)</Label>
          <Input
            id="depth"
            type="number"
            value={depth}
            onChange={(e) => setDepth(parseInt(e.target.value) || 1)}
            min={1}
            max={10}
            disabled={loading}
          />
          <p className="text-sm text-muted-foreground mt-1">
            Количество страниц результатов поиска для парсинга (1 страница ≈ 10-20 URL)
          </p>
        </div>

        <Button onClick={handleStart} disabled={loading || !keyword.trim()}>
          {loading ? "Запуск..." : "Запустить парсинг"}
        </Button>
      </CardContent>
    </Card>
  )
}
```

**Как работает связка:**

1. **Пользователь заполняет форму:**
   - Вводит ключевое слово (например: "кирпич")
   - Выбирает источник (google/yandex/both)
   - Указывает глубину (количество страниц)

2. **Frontend отправляет запрос:**
   ```typescript
   const data = await apiFetch<{ runId: string; keyword: string; status: string }>("/parsing/start", {
     method: "POST",
     body: JSON.stringify({ keyword, depth, source }),
   })
   ```

3. **Backend обрабатывает запрос:**
   - Создает запись в БД (parsing_request, parsing_run)
   - Запускает асинхронную задачу парсинга
   - Возвращает runId немедленно

4. **Parser Service выполняет парсинг (с защитой от дублирования):**
   - Проверяет, не выполняется ли уже запрос с такими же параметрами (keyword + depth + source)
   - Если запрос дублируется - возвращает пустой результат без выполнения парсинга
   - Подключается к Chrome CDP
   - Открывает **ТОЛЬКО ОДНУ** вкладку для каждого источника (google/yandex/both)
   - Собирает ссылки с результатов поиска
   - Возвращает список доменов

5. **Backend сохраняет результаты:**
   - Сохраняет домены в domains_queue
   - Обновляет статус парсинга на "completed"

6. **Frontend перенаправляет на страницу результатов:**
   ```typescript
   router.push(`/parsing-runs/${data.runId}`)
   ```

**Проверка работоспособности:**

1. Откройте `http://localhost:3000/manual-parsing`
2. Введите ключевое слово (например: "кирпич")
3. Выберите источник (google)
4. Укажите глубину (1)
5. Нажмите "Запустить парсинг"
6. **✅ КРИТИЧНО: Проверьте, что открывается только ОДНА вкладка в Chrome** (не две!)
7. После завершения вы будете перенаправлены на страницу результатов

**Ожидаемый результат:**
- Форма отправляет запрос успешно
- В окне Chrome открывается **ТОЛЬКО ОДНА** вкладка для каждого источника (google/yandex)
- Парсинг выполняется реально (не мгновенно)
- В логах Backend видно один "[DUPLICATE PREVENTION] Checking" и один "Background task added"
- В логах Parser Service видно один "[DUPLICATE CHECK] Marked request" и один "=== PARSE REQUEST ==="

**Команды для проверки:**
```powershell
# Проверить логи Backend - должен быть один Background task added для каждого run_id
Get-Content "logs\Backend-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE PREVENTION|Background task added"

# Проверить логи Parser Service - должен быть один PARSE REQUEST для каждого запроса
Get-Content "logs\Parser Service-*.log" -Tail 100 | Select-String -Pattern "DUPLICATE|PARSE REQUEST"

# Проверить через API
$body = @{ keyword = "тест"; depth = 1; source = "google" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/parsing/start -Method Post -ContentType "application/json; charset=utf-8" -Body $body
```
- После завершения происходит перенаправление на страницу результатов
- Результаты отображаются на странице `/parsing-runs/{runId}`

**⚠️ Известные ограничения:**
- **CAPTCHA:** При появлении CAPTCHA требуется ручное решение в окне Chrome (см. раздел "Известные ограничения" в 2.4 Parsing)

### 3.3 Правила работы с динамическими маршрутами

**ОБЯЗАТЕЛЬНО для Next.js 16+:**

```typescript
// ✅ ПРАВИЛЬНО
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const supplierId = parseInt(id, 10)
  
  // Валидация
  if (isNaN(supplierId) || supplierId <= 0) {
    return <div>Ошибка: Неверный ID</div>
  }
  
  return <Component supplierId={supplierId} />
}

// ❌ НЕПРАВИЛЬНО (Next.js 15 и ниже)
export default function Page({
  params,
}: {
  params: { id: string }
}) {
  const supplierId = parseInt(params.id, 10)
  // ...
}
```

### 3.4 API клиент (`lib/api.ts`)

**Правила:**
- Все HTTP запросы идут через `apiFetch()`
- Запрещено использовать `fetch()` напрямую из компонентов
- Базовый URL настраивается через переменные окружения
- Автоматическая обработка ошибок

**Формат ошибок:**
- Все ошибки оборачиваются в `APIError`
- Сообщения об ошибках - читаемые строки, не объекты

### 3.5 Обработка ошибок

**Правила:**
1. Всегда проверять тип ошибки перед выводом
2. Использовать `JSON.stringify()` для объектов ошибок
3. Показывать понятные сообщения пользователю
4. Не показывать `[object Object]`

**Пример:**
```typescript
if (error || !supplier) {
  const errorMessage = error || "Поставщик не найден"
  return (
    <div className="text-red-500 p-4">
      Ошибка: {typeof errorMessage === 'string' 
        ? errorMessage 
        : JSON.stringify(errorMessage)}
    </div>
  )
}
```

---

## 4. Правила работы с типами данных

### 4.1 Дата и время

**Backend:**
- В БД: `date` (SQLAlchemy `Date`) или `datetime` (SQLAlchemy `DateTime`)
- В DTO: `Optional[str]` (ISO строка)
- Конвертация: `date.isoformat()` или `datetime.isoformat()`
- **ОБЯЗАТЕЛЬНО:** Конвертация ПЕРЕД валидацией DTO

**Пример:**
```python
# В роутере
if isinstance(s.registration_date, date):
    registration_date_str = s.registration_date.isoformat()
else:
    registration_date_str = str(s.registration_date)

supplier_dict = {
    # ...
    'registration_date': registration_date_str,
}
supplier_dtos.append(ModeratorSupplierDTO.model_validate(supplier_dict, from_attributes=False))
```

**Frontend:**
- Все даты - строки в формате ISO
- Форматирование для отображения через `formatDate()`

### 4.2 Импорты (критически важно!)

**ОБЯЗАТЕЛЬНЫЕ правила:**

1. **Перед использованием типа:**
   - Если используешь `isinstance(obj, date)` → должен быть `from datetime import date`
   - Если используешь `isinstance(obj, datetime)` → должен быть `from datetime import datetime`

2. **При копировании кода:**
   - ОБЯЗАТЕЛЬНО копировать блок импортов вместе с кодом
   - Если копируешь функцию с `date` → копируй и `from datetime import date`

3. **При рефакторинге:**
   - НЕ удалять импорты, которые используются в коде
   - Перед удалением импорта проверить через grep

4. **Перед коммитом:**
   - Запустить `python temp/backend/check_imports.py`
   - Исправить все ошибки

### 4.3 Валидация параметров

**Backend:**
- Все path параметры валидируются FastAPI автоматически
- Query параметры имеют ограничения (`ge`, `le`, `min_length`, etc.)

**Frontend:**
- Все параметры из URL валидируются перед использованием
- `parseInt(value, 10)` с проверкой на `isNaN()`
- Проверка диапазона значений (`> 0` для ID)

**Пример:**
```typescript
const supplierId = parseInt(params.id, 10)

if (isNaN(supplierId) || supplierId <= 0) {
  return <div>Ошибка: Неверный ID поставщика</div>
}
```

---

## 5. Обработка ошибок

### 5.1 Backend

**Правила:**
- Все исключения обрабатываются глобальными обработчиками
- CORS заголовки добавляются даже к ошибкам
- Ошибки возвращают JSON с полем `detail`
- В development режиме добавляется traceback

**Структура ошибки:**
```json
{
  "detail": "Error message or traceback in development"
}
```

### 5.2 Frontend

**Правила:**
- Все ошибки API оборачиваются в `APIError`
- Показываются понятные сообщения пользователю
- Не показываются технические детали (кроме development)
- Ошибки логируются в консоль для отладки

---

## 6. CORS

**Настройки:**
- Разрешенные origins: настраиваются в `backend/app/config.py`
- Заголовки добавляются ко ВСЕМ ответам (включая ошибки)
- Методы: `*` (все)
- Credentials: разрешены

**Проверка:**
- Все ответы должны содержать `Access-Control-Allow-Origin`
- Даже при ошибках 500 CORS заголовки присутствуют

---

## 7. База данных

### 7.1 Миграции

- Все изменения схемы БД через SQL миграции
- Файлы миграций в `backend/migrations/`
- Применение: `psql -U postgres -d database -f migrations/001_initial_schema.sql`

### 7.2 Модели

- Используется SQLAlchemy 2.0
- Все модели в `backend/app/adapters/db/models.py`
- Асинхронные сессии через `AsyncSession`

---

## 8. Тестирование

### 8.1 Backend

- Unit тесты: `backend/tests/unit/`
- Integration тесты: `backend/tests/integration/`
- Contract тесты: `backend/tests/contract/`

### 8.2 Frontend

- Type checking: `npm run type-check`
- Linting: `npm run lint`
- Build проверка: `npm run build`

---

## 9. Развертывание

### 9.1 Порты

- Backend: `8000`
- Frontend: `3000` (dev), `3000` (prod)
- Parser Service: `9003`
- Chrome CDP: `9222`

### 9.2 Переменные окружения

**Backend:**
- `DATABASE_URL` - строка подключения к PostgreSQL
- `ENV` - окружение (`development` или `production`)
- `CORS_ORIGINS` - разрешенные origins (через запятую)

**Frontend:**
- `NEXT_PUBLIC_API_URL` - URL Backend API

---

## 10. Чеклист перед коммитом

**ОБЯЗАТЕЛЬНО:**

1. ✅ Запустить `python temp/backend/check_imports.py`
2. ✅ Проверить, что все используемые типы импортированы
3. ✅ Проверить валидацию параметров (особенно ID из URL)
4. ✅ Проверить обработку ошибок (не показывать `[object Object]`)
5. ✅ Проверить конвертацию дат (date → ISO string)
6. ✅ Проверить CORS заголовки (даже при ошибках)
7. ✅ Проверить, что код компилируется без ошибок
8. ✅ Обновить документацию при изменении API или поведения

---

## 11. Известные проблемы и решения

Все известные проблемы и их решения задокументированы в `docs/TROUBLESHOOTING.md`.

**Критически важные:**
- Ошибка 4: NameError с отсутствующим импортом `date`
- Ошибка 5: 422 с `NaN` в URL
- Ошибка 6: Next.js 16 async params

---

## 12. Процесс обновления спецификации

**⚠️ КРИТИЧЕСКИ ВАЖНО:**

Спецификация обновляется ТОЛЬКО после успешной проверки работоспособности.

**Правила:**
1. Перед добавлением в спецификацию - ОБЯЗАТЕЛЬНАЯ проверка
2. Если что-то не работает - помечать как "❌ Не работает" или "⚠️ Требует проверки"
3. При исправлении ошибки - сначала проверяем, потом обновляем спецификацию
4. Все изменения должны быть задокументированы в `docs/TROUBLESHOOTING.md`

**Подробнее:** см. [`docs/DIAGNOSTICS_PROCESS.md`](DIAGNOSTICS_PROCESS.md)

---

## 13. Текущий статус проекта

### Что исправлено и проверено

✅ **Проверено и работает:**
- ✅ Парсинг через Backend API (`POST /parsing/start`) - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Связка Frontend-Backend для запуска парсинга - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Интеграция Backend с Parser Service - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Chrome CDP в видимом режиме - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Открытие вкладок с поисковиками в браузере - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Сохранение результатов парсинга в базу данных - **ПРОВЕРЕНО** (2025-12-27)
- ✅ Страница `/keywords` с двойным accordion и группировкой доменов - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Страница `/parsing-runs/[runId]` с фильтрацией blacklist и статусами - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Главная страница с прогрессбаром и polling - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Автоматическое создание ключей при парсинге - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Фильтрация доменов из blacklist в результатах парсинга - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Отображение статусов доменов (Поставщик/Реселлер) - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Правильное форматирование дат с UTC - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Отображение глубины парсинга в деталях запуска - **ПРОВЕРЕНО** (2025-12-29)
- ✅ Убрано автоматическое переключение на вкладку браузера (только при капче) - **ПРОВЕРЕНО** (2025-12-29)

✅ **Исправлено (но требует проверки на реальных данных):**
- Ошибка 4: Импорт `date` в `moderator_suppliers.py` - исправлено
- Ошибка 5: Валидация ID и обработка ошибок в Frontend - исправлено
- Ошибка 6: Next.js 16 async params - исправлено
- Ошибка 3: CORS заголовки при ошибках - исправлено
- Ошибка 2: Конвертация `date` → `string` - исправлено

### Что требует диагностики и исправления

⚠️ **ТРЕБУЕТ ДИАГНОСТИКИ:**
- Все API endpoints на реальных данных с реальной БД
- Все Frontend страницы на реальных данных
- Интеграция с Checko API - ⚠️ **ИСПРАВЛЕНА** ошибка с Promise.all (Ошибка 7), но требует проверки на реальных данных
- Все CRUD операции
- Пагинация и фильтры
- Валидация всех параметров
- Edge cases

⚠️ **ТРЕБУЕТ РАБОТЫ:**
- **CAPTCHA:** Автоматическое решение CAPTCHA при парсинге (см. раздел "Известные ограничения" в 2.4 Parsing)

**Процесс:** См. [`docs/DIAGNOSTICS_PROCESS.md`](DIAGNOSTICS_PROCESS.md)

### Рекомендации для повышения эффективности

**См. раздел "Рекомендации для повышения эффективности" в [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)**

---

## 15. Рекомендации для повышения эффективности (2025-12-29)

### 15.1 Оптимизация производительности

#### Проблема: Множественные запросы при загрузке страницы `/keywords`

**Текущее состояние:**
- При загрузке страницы выполняется `N+1` запросов (1 для ключей + N для каждого ключа)
- Загружаются все поставщики и весь blacklist (до 1000 записей каждый)
- При большом количестве ключей загрузка может быть медленной

**Рекомендации:**

1. **Добавить кэширование данных поставщиков и blacklist:**
   ```typescript
   // Использовать React Context или Zustand для глобального состояния
   const [suppliersCache, setSuppliersCache] = useState<SupplierDTO[]>([])
   const [blacklistCache, setBlacklistCache] = useState<BlacklistEntryDTO[]>([])
   
   // Обновлять кэш только при изменениях
   useEffect(() => {
     // Загружать только если кэш пустой или устарел
     if (suppliersCache.length === 0 || cacheExpired) {
       loadSuppliers()
     }
   }, [])
   ```

2. **Использовать пагинацию для ключей:**
   ```typescript
   // Загружать по 10-20 ключей за раз
   const [page, setPage] = useState(1)
   const keywordsData = await getKeywords({ limit: 20, offset: (page - 1) * 20 })
   ```

3. **Ленивая загрузка URL для ключей:**
   ```typescript
   // Загружать URL только при раскрытии accordion
   const [expandedKeywords, setExpandedKeywords] = useState<Set<number>>(new Set())
   
   useEffect(() => {
     expandedKeywords.forEach(keywordId => {
       // Загрузить URL только для раскрытых ключей
       loadUrlsForKeyword(keywordId)
     })
   }, [expandedKeywords])
   ```

4. **Добавить индексы в БД:**
   ```sql
   -- Для ускорения запросов по keyword и domain
   CREATE INDEX idx_domains_queue_keyword ON domains_queue(keyword);
   CREATE INDEX idx_domains_queue_domain ON domains_queue(domain);
   CREATE INDEX idx_suppliers_domain ON moderator_suppliers(domain);
   ```

**Приоритет:** Высокий

#### Проблема: Загрузка всех поставщиков и blacklist на странице `/parsing-runs/[runId]`

**Рекомендации:**
- Кэшировать blacklist в localStorage (обновлять только при изменениях)
- Использовать более эффективную структуру данных (Set вместо массива)
- Рассмотреть добавление endpoint для проверки статуса одного домена

**Приоритет:** Средний

### 15.2 Улучшение UX

#### Прогрессбар парсинга

**Текущее состояние:** Показывает только статус "running" или "completed"

**Рекомендации:**
1. Добавить отображение процента выполнения (если backend может предоставить)
2. Добавить отображение количества найденных URL в реальном времени
3. Добавить возможность отмены парсинга
4. Добавить звуковое уведомление при завершении

**Пример улучшения:**
```typescript
// Backend может возвращать прогресс
interface ParsingProgress {
  status: "running" | "completed" | "failed"
  progress?: number  // 0-100
  urlsFound?: number
  canCancel?: boolean
}
```

**Приоритет:** Средний

#### Автоматическое обновление данных

**Рекомендации:**
1. Добавить WebSocket или Server-Sent Events для real-time обновлений
2. Добавить polling для автоматического обновления списка ключей
3. Добавить уведомления о новых результатах парсинга
4. Добавить индикатор новых данных (badge с количеством)

**Приоритет:** Низкий

### 15.3 Улучшение функциональности

#### Группировка и фильтрация доменов

**Рекомендации:**
1. Добавить сортировку доменов (по количеству URL, по алфавиту)
2. Добавить поиск по доменам в результатах парсинга
3. Добавить фильтрацию по статусу (только поставщики, только реселлеры, только новые)
4. Добавить экспорт результатов в CSV/Excel

**Приоритет:** Низкий

#### Обработка ошибок

**Рекомендации:**
1. Добавить retry механизм для неудачных API запросов
2. Добавить более детальные сообщения об ошибках
3. Добавить логирование ошибок на стороне клиента
4. Добавить отправку ошибок на сервер для анализа

**Пример:**
```typescript
// Retry механизм
async function apiFetchWithRetry<T>(endpoint: string, options?: RequestInit, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await apiFetch<T>(endpoint, options)
    } catch (error) {
      if (i === retries - 1) throw error
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
    }
  }
  throw new Error("Max retries exceeded")
}
```

**Приоритет:** Средний

### 15.4 Оптимизация парсера

#### Переключение вкладок браузера

**Текущее состояние:** Переключение происходит только при капче ✅

**Рекомендации:**
1. Добавить настройку для пользователя: всегда переключать/никогда переключать/только при капче
2. Добавить визуальное уведомление в UI при обнаружении капчи (вместо только звукового сигнала)
3. Добавить счетчик времени ожидания капчи в UI

**Приоритет:** Низкий

### 15.5 Документация и тестирование

**Рекомендации:**
1. Добавить интерактивные примеры API запросов в документацию
2. Добавить диаграммы потоков данных для сложных операций
3. Добавить видео-туториалы для основных операций
4. Добавить автоматические тесты для критических связок Backend-Frontend
5. Добавить E2E тесты для основных пользовательских сценариев

**Приоритет:** Средний

### 15.6 Мониторинг и аналитика

**Рекомендации:**
1. Добавить мониторинг производительности API запросов
2. Добавить аналитику использования функций (какие страницы чаще используются)
3. Добавить логирование действий пользователя для анализа UX
4. Добавить метрики времени загрузки страниц

**Приоритет:** Низкий

---

### Итоговые приоритеты рекомендаций

**Высокий приоритет:**
1. Оптимизация производительности загрузки данных (кэширование, пагинация, ленивая загрузка)
2. Добавление индексов в БД для ускорения запросов

**Средний приоритет:**
1. Улучшение UX прогрессбара (процент выполнения, количество URL)
2. Оптимизация фильтрации blacklist (кэширование)
3. Улучшение обработки ошибок (retry механизм)
4. Добавление автоматических тестов

**Низкий приоритет:**
1. Автоматическое обновление данных (WebSocket/polling)
2. Улучшение группировки и фильтрации доменов
3. Настройки переключения вкладок браузера
4. Мониторинг и аналитика

---

## 14. История изменений

- **2025-12-26**: Создана первая версия спецификации
- **2025-12-26**: Добавлены статусы проверки и правила обновления
- **2025-12-26**: Уточнено, что спецификация отражает ТОЛЬКО проверенное состояние
- **2025-12-26**: Добавлены статусы для всех endpoints и страниц
- **2025-12-26**: Добавлен раздел "Текущий статус проекта" с указанием, что требует диагностики
- **2025-12-27**: ✅ Добавлена полная документация рабочей связки Backend-Frontend для парсинга с полным кодом
- **2025-12-27**: ✅ Обновлен статус парсинга на "ПРОВЕРЕНО И РАБОТАЕТ"
- **2025-12-27**: ✅ Добавлена документация Frontend компонента `/manual-parsing` с полным кодом
- **2025-12-27**: ⚠️ Добавлено предупреждение о необходимости работы над CAPTCHA
- **2025-12-29**: ✅ Добавлена документация страницы `/keywords` с двойным accordion и группировкой доменов
- **2025-12-29**: ✅ Добавлена документация страницы `/parsing-runs/[runId]` с фильтрацией blacklist и статусами
- **2025-12-29**: ✅ Добавлена документация главной страницы с прогрессбаром и polling
- **2025-12-29**: ✅ Добавлена документация автоматического создания ключей при парсинге
- **2025-12-29**: ✅ Добавлены рекомендации по оптимизации производительности и улучшению UX
- **2025-12-29**: ✅ Добавлена документация определения источников для доменов (Google/Яндекс) с полным описанием потока данных
- **2025-12-29**: ✅ Создана карта проекта (`docs/PROJECT_MAP.md`) с описанием всех директорий и ключевых файлов
- **2025-12-29**: ✅ Созданы рекомендации по улучшению работы AI-агента (`docs/AI_AGENT_IMPROVEMENTS.md`)
- **2025-12-30**: ✅ Добавлена полная документация связок Backend-Frontend для Suppliers (список, детали, редактирование)
- **2025-12-30**: ✅ Добавлена документация интеграции с Checko API и карточки поставщика с Checko данными

---

**Помни: Эта спецификация отражает РЕАЛЬНОЕ состояние системы. Обновляй её ТОЛЬКО после проверки работоспособности!**

