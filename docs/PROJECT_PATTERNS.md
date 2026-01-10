# Паттерны проекта B2B Platform

**⚠️ ВАЖНО: Этот документ содержит правильные паттерны, используемые в проекте. При изменении кода ОБЯЗАТЕЛЬНО сверяться с этими паттернами!**

**📚 Связанные документы:**
- **Правила работы**: [`.cursorrules`](../.cursorrules)
- **Библия ошибок**: [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- **Критические точки**: [`docs/CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md`](CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md)

---

## Frontend паттерны

### 1. Checkbox + AccordionTrigger

**Проблема:** `Checkbox` рендерится как `<button>`, `AccordionTrigger` тоже рендерится как `<button>`. Вложенные кнопки вызывают ошибку гидратации React.

**✅ ПРАВИЛЬНЫЙ паттерн:**

```tsx
<div className="flex items-center">
  <Checkbox
    checked={isSelected}
    onCheckedChange={() => toggleSelection(item.id)}
    onClick={(e) => e.stopPropagation()}
  />
  <AccordionTrigger className="hover:no-underline flex-1 py-1">
    <div className="flex items-center gap-2 flex-1">
      {/* Содержимое аккордеона */}
    </div>
  </AccordionTrigger>
</div>
```

**Примеры в проекте:**
- ✅ `frontend/moderator-dashboard-ui/app/keywords/page.tsx` (строки 394-402)
- ✅ `frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx` (строки 900-950) - исправлено

**❌ ЗАПРЕЩЕНО:**

```tsx
// ❌ НЕПРАВИЛЬНО - Checkbox внутри AccordionTrigger
<AccordionTrigger>
  <Checkbox /> {/* Вызовет hydration error! */}
  ...
</AccordionTrigger>
```

**Почему это важно:**
- HTML не позволяет вложенные кнопки
- React/Next.js выдает ошибку гидратации
- Нарушает семантику HTML

---

### 2. Группировка доменов

**✅ ПРАВИЛЬНЫЙ паттерн:**

```typescript
import { groupByDomain, extractRootDomain } from "@/lib/utils-domain"

// Всегда нормализовать домены перед сравнением
const normalizedDomain = extractRootDomain(domain).toLowerCase()

// Группировка доменов
const grouped = groupByDomain(domainsArray)
```

**Примеры в проекте:**
- `frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx` (строки 286-305)
- `frontend/moderator-dashboard-ui/app/keywords/page.tsx` (строки 190-204)

**Правила:**
1. **Всегда нормализовать домены:** `extractRootDomain(domain).toLowerCase()`
2. **Использовать `groupByDomain()` из `lib/utils-domain`**
3. **Фильтрация blacklist ПЕРЕД группировкой**

**❌ ЗАПРЕЩЕНО:**

```typescript
// ❌ НЕПРАВИЛЬНО - сравнение без нормализации
if (domain === blacklistedDomain) { ... }

// ✅ ПРАВИЛЬНО
const rootDomain = extractRootDomain(domain).toLowerCase()
if (rootDomain === extractRootDomain(blacklistedDomain).toLowerCase()) { ... }
```

---

### 3. Кэширование данных

**✅ ПРАВИЛЬНЫЙ паттерн:**

```typescript
import { 
  getCachedSuppliers, 
  setCachedSuppliers, 
  invalidateSuppliersCache 
} from "@/lib/cache"

// Загрузка с кэшем
const cached = getCachedSuppliers()
if (cached) {
  setSuppliers(cached)
}

// Загрузка свежих данных
const fresh = await getSuppliers()
setCachedSuppliers(fresh.suppliers)
setSuppliers(fresh.suppliers)

// Инвалидация после изменений
await updateSupplier(id, data)
invalidateSuppliersCache()
```

**Примеры в проекте:**
- `frontend/moderator-dashboard-ui/lib/cache.ts` - функции кэширования
- `frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx` - использование кэша

**Правила:**
1. **Blacklist всегда загружается свежим** (не из кэша) при отображении результатов
2. **Кэш инвалидируется после изменений** (создание, обновление, удаление)
3. **Использовать функции из `lib/cache.ts`**

**❌ ЗАПРЕЩЕНО:**

```typescript
// ❌ НЕПРАВИЛЬНО - использовать кэш blacklist при отображении результатов
const blacklist = getCachedBlacklist()

// ✅ ПРАВИЛЬНО - всегда загружать свежий blacklist
const blacklist = await getBlacklist({ limit: 1000 })
```

---

### 4. Работа с состояниями

**✅ ПРАВИЛЬНЫЙ паттерн:**

```typescript
// Использование Set для множественных выборов
const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())

// Добавление/удаление из Set
const toggleSelection = (id: string) => {
  setSelectedItems((prev) => {
    const newSet = new Set(prev)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    return newSet
  })
}

// Использование Map для кэширования результатов
const [resultsMap, setResultsMap] = useState<Map<string, Result>>(new Map())
```

**Примеры в проекте:**
- `frontend/moderator-dashboard-ui/app/parsing-runs/[runId]/page.tsx` - `selectedDomains`, `innResultsMap`

---

## Backend паттерны

### 1. Структура usecases

**✅ ПРАВИЛЬНЫЙ паттерн:**

```python
# backend/app/usecases/example_usecase.py
import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.db.repositories import SomeRepository

logger = logging.getLogger(__name__)

async def execute(db: AsyncSession, param1: str, param2: int) -> Dict[str, Any]:
    """
    Описание usecase.
    
    Args:
        db: Database session
        param1: Описание параметра
        param2: Описание параметра
        
    Returns:
        Dict с результатами
    """
    try:
        repo = SomeRepository(db)
        # Бизнес-логика
        result = await repo.some_method(param1)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in execute: {e}", exc_info=True)
        raise
```

**Примеры в проекте:**
- `backend/app/usecases/extract_inn_batch.py`
- `backend/app/usecases/create_supplier.py`

**Правила:**
1. **Функция называется `execute`**
2. **Первый параметр - `db: AsyncSession`**
3. **Возвращает `Dict[str, Any]`**
4. **Логирование ошибок с `exc_info=True`**
5. **Использование репозиториев для работы с БД**

---

### 2. Работа с репозиториями

**✅ ПРАВИЛЬНЫЙ паттерн:**

```python
from app.adapters.db.repositories import SomeRepository

async def execute(db: AsyncSession, domain: str) -> Dict[str, Any]:
    repo = SomeRepository(db)
    
    # Получение данных
    item = await repo.get_by_domain(domain)
    if not item:
        return {"status": "error", "message": "Not found"}
    
    # Обновление данных
    item.field = new_value
    await repo.update(item)
    
    return {"status": "success", "data": item}
```

**Примеры в проекте:**
- `backend/app/adapters/db/repositories.py` - все репозитории
- `backend/app/usecases/extract_inn_batch.py` - использование репозиториев

**Правила:**
1. **Создавать репозиторий внутри usecase**
2. **Использовать методы репозитория для работы с БД**
3. **Не писать SQL напрямую в usecases**

---

### 3. Обработка ошибок

**✅ ПРАВИЛЬНЫЙ паттерн:**

```python
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

async def execute(db: AsyncSession, param: str) -> Dict[str, Any]:
    try:
        # Бизнес-логика
        result = await some_operation(param)
        return {"status": "success", "data": result}
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Правила:**
1. **Логировать все ошибки**
2. **Использовать `exc_info=True` для неожиданных ошибок**
3. **Возвращать понятные сообщения об ошибках**
4. **Использовать правильные HTTP статусы**

---

## Анти-паттерны

### 1. Button внутри button

**❌ ЗАПРЕЩЕНО:**

```tsx
<button>
  <Checkbox /> {/* ❌ Button внутри button */}
  <AccordionTrigger> {/* ❌ Button внутри button */}
</button>
```

**Почему:**
- HTML не позволяет вложенные кнопки
- React/Next.js выдает ошибку гидратации
- Нарушает семантику и доступность

**✅ ПРАВИЛЬНО:**

```tsx
<div>
  <Checkbox /> {/* ✅ Вне button */}
  <AccordionTrigger> {/* ✅ Вне button */}
</div>
```

---

### 2. A внутри a

**❌ ЗАПРЕЩЕНО:**

```tsx
<a href="...">
  <a href="..."> {/* ❌ Ссылка внутри ссылки */}
</a>
```

**✅ ПРАВИЛЬНО:**

```tsx
<div>
  <a href="...">Ссылка 1</a>
  <a href="...">Ссылка 2</a>
</div>
```

---

### 3. Неправильная структура компонентов

**❌ ЗАПРЕЩЕНО:**

```tsx
// Добавление функционала в проблемную структуру
<AccordionTrigger>
  <Checkbox /> {/* Проблемная структура */}
  {/* Новый функционал */}
</AccordionTrigger>
```

**✅ ПРАВИЛЬНО:**

```tsx
// Сначала исправить структуру, потом добавлять функционал
<div>
  <Checkbox /> {/* Исправленная структура */}
  <AccordionTrigger>
    {/* Новый функционал */}
  </AccordionTrigger>
</div>
```

---

## Чеклист перед изменениями

**Перед изменением компонента/структуры ОБЯЗАТЕЛЬНО:**

1. [ ] Найти аналогичные места в проекте через `codebase_search`
2. [ ] Изучить правильные паттерны в других файлах
3. [ ] Проверить `docs/PROJECT_PATTERNS.md` на наличие паттерна
4. [ ] Проверить комментарии в коде на наличие важных решений
5. [ ] Если структура проблемная - исправить ПЕРЕД добавлением функционала
6. [ ] Если паттерна нет в документации - добавить после реализации

---

**Дата создания:** 2025-12-29  
**Последнее обновление:** 2025-12-29





