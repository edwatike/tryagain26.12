# Comet Integration Documentation

**Дата:** 2026-01-10  
**Статус:** ✅ Реализовано и работает  
**Версия:** 1.0

---

## 📋 Обзор

Comet Integration - это AI-ассистент для извлечения ИНН и email с веб-сайтов компаний. Интеграция позволяет автоматически находить контактную информацию и реквизиты компаний на их сайтах.

## 🏗️ Архитектура

### Компоненты:

1. **Backend (FastAPI)**
   - `backend/app/transport/routers/comet.py` - API роутер
   - `backend/app/transport/schemas/comet.py` - Pydantic схемы
   - `experiments/comet-integration/test_single_domain.py` - скрипт ассистента

2. **Frontend (Next.js)**
   - `frontend/moderator-dashboard-ui/lib/api.ts` - API функции
   - `frontend/moderator-dashboard-ui/lib/types.ts` - TypeScript типы
   - `frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx` - UI компоненты

3. **Chrome CDP**
   - Подключение к существующему Chrome CDP (порт 9222)
   - Использование browser automation для навигации по сайтам

## 🔄 Процесс работы

### 1. Запуск через Frontend
```typescript
// Пользователь выбирает домены и нажимает кнопку "Comet"
const resp = await startCometExtractBatch(runId, domainsArray)
```

### 2. Backend обработка
```python
# Создается фоновая задача для обработки доменов
task = asyncio.create_task(_process_comet_batch(comet_run_id, run_id, domains))
```

### 3. Запуск AI-ассистента
```python
# Для каждого домена запускается скрипт Comet
process = await asyncio.create_subprocess_exec(
    python_exe,
    script_path,
    "--domain", domain,
    "--json"
)
```

### 4. Извлечение данных
AI-ассистент:
- Подключается к Chrome CDP
- Открывает сайт компании
- Ищет разделы "Контакты", "О компании", "Реквизиты"
- Извлекает ИНН (10-12 цифр) и email
- Возвращает результат в JSON формате

### 5. Сохранение результатов
```python
# Результаты сохраняются в process_log parsing run
process_log["comet"]["runs"][comet_run_id] = {
    "status": "completed",
    "results": results
}
```

### 6. Автоматическое создание поставщиков
```typescript
// Frontend автоматически создает/обновляет поставщиков
const autoUpsert = async (domain: string, res: CometExtractionResult) => {
  if (res.inn || res.email) {
    await createOrUpdateSupplier(domain, res.inn, res.email)
    if (res.inn) {
      const checkoData = await getCheckoData(res.inn)
      // Сохранение Checko данных
    }
  }
}
```

## 📊 API Endpoints

### POST `/comet/extract-batch`
Запуск batch извлечения для доменов

**Request:**
```json
{
  "runId": "c3e59c47-010e-4325-b131-3a8e86853d06",
  "domains": ["russteels.ru", "gremir.ru"]
}
```

**Response:**
```json
{
  "runId": "c3e59c47-010e-4325-b131-3a8e86853d06",
  "cometRunId": "comet_20260110_134530_5c66e9aa"
}
```

### GET `/comet/status/{runId}?cometRunId={id}`
Получение статуса извлечения

**Response:**
```json
{
  "runId": "c3e59c47-010e-4325-b131-3a8e86853d06",
  "cometRunId": "comet_20260110_134530_5c66e9aa",
  "status": "completed",
  "processed": 2,
  "total": 2,
  "results": [
    {
      "domain": "russteels.ru",
      "status": "success",
      "inn": "5050089420",
      "email": "info@russteels.ru",
      "sourceUrls": ["https://russteels.ru/company/requisites/", "https://russteels.ru/contacts/"]
    }
  ]
}
```

## 🎯 TypeScript типы

### CometExtractionResult
```typescript
interface CometExtractionResult {
  domain: string
  status: "pending" | "running" | "success" | "not_found" | "error"
  inn: string | null
  email: string | null
  sourceUrls: string[]
  error?: string | null
}
```

### CometStatusResponse
```typescript
interface CometStatusResponse {
  runId: string
  cometRunId: string
  status: "running" | "completed" | "failed"
  processed: number
  total: number
  results: CometExtractionResult[]
}
```

## 🔧 Конфигурация

### Переменные окружения
- `COMET_SCRIPT_PATH` - путь к скрипту ассистента
- `COMET_TIMEOUT` - таймаут выполнения (по умолчанию 180 секунд)
- `CHROME_CDP_URL` - URL Chrome CDP (по умолчанию `http://127.0.0.1:9222`)

### Настройки скрипта
- **Таймаут:** 120 секунд для ответа ассистента
- **Источники:** Google, Yandex для поиска страниц
- **Кодировка:** UTF-8/CP1251 для Windows

## 🎨 UI Компоненты

### Кнопка "Comet"
```typescript
<Button
  onClick={handleCometExtract}
  disabled={cometLoading}
  className="h-8 text-xs bg-black hover:bg-black/90 text-white"
>
  Comet ({selectedDomains.size})
</Button>
```

### Индикаторы статуса
- **Comet...** - идет извлечение
- **Comet ИНН: {inn}** - ИНН найден
- **Comet email: {email}** - email найден

## 📈 Интеграция с Checko

При нахождении ИНН:
1. Автоматически запрашиваются данные Checko
2. Данные сохраняются в карточку поставщика
3. Отображаются в UI поставщика

## 🚀 Производительность

### Оптимизации:
- **Background tasks** - обработка в фоновом режиме
- **In-memory storage** - кэш результатов
- **Batch processing** - обработка нескольких доменов
- **Retry mechanism** - повторные попытки при ошибках

### Таймауты:
- **Скрипт Comet:** 180 секунд
- **AI ассистент:** 120 секунд
- **HTTP запросы:** 30 секунд

## 🔒 Безопасность

### Защиты:
- **Валидация доменов** - проверка формата
- **Санитизация ИНН** - только цифры
- **Rate limiting** - ограничение запросов
- **Error handling** - безопасная обработка ошибок

## 🐛 Отладка

### Логирование:
```python
logger.info(f"Processing Comet batch {comet_run_id} for {len(domains)} domains")
logger.info(f"Comet script completed for {domain}")
logger.info(f"Parsed Comet result: status={result.get('status')}")
```

### Frontend логирование:
```typescript
console.log('[Comet] Button clicked')
console.log('[Comet] AutoUpsert Processing domain:', res)
```

## 📝 Тестирование

### Тестовые домены:
- **russteels.ru** - ИНН: 5050089420, Email: info@russteels.ru
- **gremir.ru** - Email: zakaz@gremir.ru
- **maxidom.ru** - ИНН: 7804064663, Email: pred@maxidom.ru

### Проверка работоспособности:
```bash
# Запуск скрипта напрямую
python experiments/comet-integration/test_single_domain.py --domain russteels.ru --json

# Проверка через API
curl -X POST "http://127.0.0.1:8000/comet/extract-batch" \
  -H "Content-Type: application/json" \
  -d '{"runId":"test","domains":["russteels.ru"]}'
```

## 🔮 Будущие улучшения

### Планируется:
1. **Мультиязычность** - поддержка сайтов на разных языках
2. **Дополнительные поля** - телефон, адрес, директор
3. **Валидация ИНН** - проверка контрольных сумм
4. **Кэширование** - Redis для результатов
5. **WebSocket** - real-time обновления

## 📞 Поддержка

### Проблемы и решения:
- **Скрипт не найден** - проверьте путь в `_run_comet_for_domain`
- **Кодировка** - используйте CP1251 для Windows
- **Chrome CDP** - убедитесь что Chrome запущен с `--remote-debugging-port=9222`
- **Timeout** - увеличьте таймаут для сложных сайтов

---

**Связанные документы:**
- [MASTER_INSTRUCTION.md](MASTER_INSTRUCTION.md) - общая архитектура
- [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) - API спецификация
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - решение проблем
