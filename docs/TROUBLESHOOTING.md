# Библия ошибок и решений

**⚠️ ВАЖНО: Этот документ является "БИБЛИЕЙ" ошибок и решений. Все ошибки и их решения ОБЯЗАТЕЛЬНО документируются здесь и НЕ ДОЛЖНЫ быть удалены или изменены без крайней необходимости.**

**📚 Связанные документы:**
- **Главная точка входа**: [`docs/DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) - индекс всей документации
- **Правила работы**: [`.cursorrules`](../../.cursorrules) - правила для AI-агента
- **Общее описание**: [`README.md`](../../README.md)

## Принципы документирования

1. **Каждая ошибка** должна быть задокументирована с:
   - Описанием проблемы
   - Причиной возникновения
   - Решением
   - Командами для проверки/воспроизведения
   - Ссылками на измененные файлы

2. **Решения НЕ должны быть удалены** даже если кажется, что проблема больше не актуальна

3. **При повторении ошибки** сначала проверяй этот документ

---

## Ошибка 1: 500 Internal Server Error на `/moderator/suppliers` - несколько процессов на порту 8000

### Описание проблемы
- Endpoint `/moderator/suppliers` возвращает 500 Internal Server Error
- CORS заголовки отсутствуют в ответе
- Логи НЕ появляются в терминале Backend (ни middleware, ни endpoint не вызываются)
- Ошибка происходит ДО того, как запрос доходит до FastAPI
- Другие endpoints (`/health`, `/`) работают нормально

### Причина
**На порту 8000 слушали несколько процессов Backend одновременно.** Запрос шел не к тому процессу, который был обновлен с последними изменениями кода.

### Решение
1. Остановить ВСЕ процессы на порту 8000:
   ```powershell
   Get-Process | Where-Object {$_.Id -in @(PID_LIST)} | Stop-Process -Force
   ```

2. Проверить, что порт свободен:
   ```powershell
   netstat -ano | Select-String ":8000"
   ```

3. Запустить только ОДИН процесс Backend:
   ```powershell
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Проверка
```bash
curl -H "Origin: http://localhost:3000" "http://127.0.0.1:8000/moderator/suppliers?limit=1&offset=0"
```

Ожидаемый результат: `200 OK` с данными в JSON формате и CORS заголовками.

### Измененные файлы
- Не требовалось изменений в коде
- Проблема была в конфигурации/запуске сервисов

### Дата решения
2025-12-26

---

## Ошибка 2: ValidationError - `registration_date` ожидает строку, получает `datetime.date`

### Описание проблемы
- Endpoint `/moderator/suppliers` возвращает 500 Internal Server Error
- В логах/ответе: `ValidationError: 1 validation error for ModeratorSupplierDTO registration_date Input should be a valid string [type=string_type, input_value=datetime.date(2005, 7, 15), input_type=date]`
- Ошибка происходит в `backend/app/transport/routers/moderator_suppliers.py` на строке 121 при вызове `ModeratorSupplierDTO.model_validate(s)`

### Причина
В модели БД (`ModeratorSupplierModel`) поле `registration_date` имеет тип `date` (SQLAlchemy `Date`), а в DTO (`ModeratorSupplierDTO`) поле `registrationDate` определено как `Optional[str]`. При использовании `model_validate()` с `from_attributes=True`, Pydantic получает объект `datetime.date` из модели, но ожидает строку.

### Решение
Конвертировать `date` объект в строку ПЕРЕД валидацией в роутере:

```python
# В backend/app/transport/routers/moderator_suppliers.py
from datetime import date

# В функции list_suppliers:
supplier_dtos = []
for s in suppliers:
    # Convert date fields to strings before validation
    registration_date_str = None
    if s.registration_date:
        if isinstance(s.registration_date, date):
            registration_date_str = s.registration_date.isoformat()
        else:
            registration_date_str = str(s.registration_date)
    
    supplier_dict = {
        'id': s.id,
        'name': s.name,
        # ... другие поля ...
        'registration_date': registration_date_str,
        # ... остальные поля ...
    }
    supplier_dtos.append(ModeratorSupplierDTO.model_validate(supplier_dict, from_attributes=False))
```

### Альтернативное решение (не использовано, но может быть полезно)
Добавить `field_validator` в DTO:

```python
# В backend/app/transport/schemas/moderator_suppliers.py
from datetime import date
from pydantic import field_validator

class ModeratorSupplierDTO(BaseDTO):
    # ... поля ...
    registrationDate: Optional[str] = Field(None, alias="registration_date")
    
    @field_validator('registrationDate', mode='before')
    @classmethod
    def convert_registration_date(cls, v):
        """Convert date object to string."""
        if isinstance(v, date):
            return v.isoformat()
        return v
```

**Примечание:** Этот подход может не работать с `from_attributes=True`, поэтому предпочтительнее конвертация в роутере.

### Проверка
```bash
curl -H "Origin: http://localhost:3000" "http://127.0.0.1:8000/moderator/suppliers?limit=1&offset=0"
```

Ожидаемый результат: `200 OK` с данными, где `registrationDate` является строкой в формате ISO (например, `"2005-07-15"`).

### Измененные файлы
- `backend/app/transport/routers/moderator_suppliers.py` - добавлена конвертация `date` в строку
- `backend/app/transport/schemas/moderator_suppliers.py` - добавлен импорт `date` (опционально, для валидатора)

### Дата решения
2025-12-26

---

## Ошибка 3: CORS заголовки отсутствуют при 500 ошибке

### Описание проблемы
- При возникновении 500 ошибки CORS заголовки не добавляются к ответу
- Frontend получает ошибку: `Access to fetch at '...' from origin '...' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present`

### Причина
CORS middleware добавляет заголовки только к успешным ответам. При возникновении исключения до того, как ответ проходит через middleware, заголовки не добавляются.

### Решение
Добавить глобальные обработчики исключений, которые добавляют CORS заголовки даже при ошибках:

```python
# В backend/app/main.py

# 1. Добавить обработчик на уровне Starlette (ДО middleware)
from starlette.requests import Request as StarletteRequest

async def starlette_exception_handler(request: StarletteRequest, exc: Exception):
    """Starlette-level exception handler."""
    import sys
    import traceback
    print(f"=== STARLETTE EXCEPTION: {type(exc).__name__}: {exc} ===", file=sys.stderr, flush=True)
    
    error_detail = f"{type(exc).__name__}: {str(exc)}"
    if settings.ENV == "development":
        error_detail += f"\n{traceback.format_exc()}"
    
    response = JSONResponse(
        status_code=500,
        content={"detail": error_detail}
    )
    
    # Добавляем CORS заголовки вручную
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

app.add_exception_handler(Exception, starlette_exception_handler)

# 2. Добавить middleware для обработки ошибок с CORS
from starlette.middleware.base import BaseHTTPMiddleware

class CORSExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления CORS заголовков к ошибкам."""
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            # Убедимся, что CORS заголовки есть даже при ошибках
            origin = request.headers.get("origin")
            if origin and origin in settings.cors_origins_list:
                if "Access-Control-Allow-Origin" not in response.headers:
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        except Exception as exc:
            # Обработка исключений на уровне middleware
            import traceback
            error_detail = f"{type(exc).__name__}: {str(exc)}"
            if settings.ENV == "development":
                error_detail += f"\n{traceback.format_exc()}"
            
            response = JSONResponse(
                status_code=500,
                content={"detail": error_detail}
            )
            
            origin = request.headers.get("origin")
            if origin and origin in settings.cors_origins_list:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
            
            return response

app.add_middleware(CORSExceptionMiddleware)
```

**ВАЖНО:** Обработчики исключений должны быть зарегистрированы ДО включения роутеров!

### Проверка
1. Создать endpoint, который вызывает исключение
2. Запросить его с Frontend
3. Проверить, что ответ содержит CORS заголовки

### Измененные файлы
- `backend/app/main.py` - добавлены обработчики исключений и CORSExceptionMiddleware

### Дата решения
2025-12-26

---

## Общие рекомендации по отладке

### Если endpoint возвращает 500, но логи не появляются:

1. **Проверь, сколько процессов слушают порт:**
   ```powershell
   netstat -ano | Select-String ":8000"
   ```

2. **Останови все процессы и запусти только один:**
   ```powershell
   Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force
   ```

3. **Проверь, что изменения в коде применились:**
   - Backend должен перезагрузиться автоматически при изменении файлов (если используется `--reload`)
   - Если нет - перезапусти вручную

### Если ошибка валидации Pydantic:

1. **Проверь типы полей в модели БД и DTO:**
   - Модель БД может возвращать `date`, а DTO ожидать `str`
   - Модель БД может возвращать `datetime`, а DTO ожидать `str`

2. **Конвертируй типы ПЕРЕД валидацией:**
   - Используй `.isoformat()` для `date` и `datetime`
   - Используй `str()` для других типов

3. **Используй `from_attributes=False` при валидации словаря:**
   ```python
   ModeratorSupplierDTO.model_validate(supplier_dict, from_attributes=False)
   ```

---

## История изменений

- **2025-12-26**: Создан документ с первыми тремя критическими ошибками и их решениями

