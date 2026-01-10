# Отчет о тестировании агента на mc.ru

**Дата тестирования:** 2025-12-31 13:24:40  
**Домен:** mc.ru  
**URL:** https://mc.ru

## Результаты тестирования

### Общая информация
- **Время работы:** 43.25 секунды
- **Успех:** True (но найден неправильный ИНН!)
- **Найденный ИНН:** 663623088192
- **Источник:** localStorage, ключ: `_ym25517528_lsid`
- **Попыток:** 1
- **Действий:** 2

### Действия агента
1. Navigated to https://mc.ru
2. Found INN via fallback CDP: 663623088192

### Критическая проблема
**Агент нашел НЕПРАВИЛЬНЫЙ ИНН!**

Найденный ИНН `663623088192` - это **ID Яндекс.Метрики** (ключ `_ym25517528_lsid`), а не ИНН компании.

**Признаки неправильного ИНН:**
- Ключ localStorage содержит `_ym` (префикс Яндекс.Метрики)
- `lsid` означает "Local Storage ID" - это ID сессии метрики
- Это 12-значное число, которое случайно соответствует формату ИНН (12 цифр)
- Нет контекста "ИНН", "реквизиты", "компания" и т.д.

## Проблемы

### 1. Проблема с неправильным ИНН

**Описание:** Агент находит ID метрик/трекинга в localStorage и принимает их за ИНН компании.

**Детали:**
- Найденный ИНН: `663623088192`
- Источник: `localStorage`, ключ: `_ym25517528_lsid`
- `_ym` - префикс Яндекс.Метрики
- Это ID сессии Яндекс.Метрики, а не ИНН компании

**Место в коде:**
- `ollama_inn_extractor/app/agents/browser_agent.py` - метод `search_inn_in_storage()` (строки 621-690)
- `ollama_inn_extractor/app/agents/browser_agent.py` - метод `search_inn_comprehensive()` (строки 700-800)

**Проблемный код:**
```python
# В search_inn_in_storage() - нет фильтрации ключей метрик
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const value = localStorage.getItem(key);
    if (value) {
        const matches = value.match(innPattern);
        // Нет проверки, что key не является ключом метрики!
```

**Последствия:**
- Агент возвращает неправильный ИНН
- Задача не выполнена (найден не ИНН компании)
- Пользователь получает неверную информацию

**Рекомендации:**
1. Добавить фильтрацию ключей localStorage/sessionStorage:
   - Исключать ключи с префиксами: `_ym*`, `_ga*`, `gtag*`, `_gid*`, `_fbp*`, `_fbc*`
   - Исключать ключи, содержащие: `tracking`, `analytics`, `metric`, `session`, `cookie`
2. Добавить проверку контекста значения:
   - Исключать значения, которые не содержат контекстных слов: "ИНН", "реквизиты", "компания"
3. Приоритизировать источники:
   - DOM (видимые элементы) > HTML > storage
   - Storage должен быть последним источником

### 2. Проблема со скоростью

**Описание:** Агент работает медленно из-за таймаутов AI.

**Детали:**
- Общее время: 43.25 секунды
- AI таймаут: 30 секунд (Ollama не успевает ответить)
- Fallback CDP search: ~1 секунда
- Навигация: ~1 секунда
- Остальное время: ~11 секунд (подключение, получение данных)

**Место в коде:**
- `ollama_inn_extractor/app/agents/interactive_inn_finder.py` - строка 241: `timeout=30`

**Проблемный код:**
```python
decision = await asyncio.wait_for(
    self.decision_engine.decide_next_action(...),
    timeout=30  # 30 seconds for AI decision (increased for better reliability)
)
```

**Последствия:**
- Медленная работа агента
- Пользователь ждет 30+ секунд на каждую попытку
- Если AI не отвечает, агент ждет полный таймаут

**Рекомендации:**
1. Уменьшить таймаут AI до 10-15 секунд
2. Использовать fallback раньше, если AI не отвечает
3. Параллелизировать запросы (если возможно)
4. Кэшировать результаты AI для похожих страниц

### 3. Проблема с отсутствием фильтрации

**Описание:** Агент не фильтрует результаты из localStorage/sessionStorage на предмет метрик/трекинга.

**Детали:**
- Нет проверки ключей на метрики/трекинг (`_ym*`, `_ga*`, `gtag*`, и т.д.)
- Нет проверки контекста (является ли число реальным ИНН компании)
- Нет приоритизации источников (DOM > HTML > storage)

**Место в коде:**
- `ollama_inn_extractor/app/agents/browser_agent.py` - метод `search_inn_comprehensive()` (строки 700-800)
- `ollama_inn_extractor/app/agents/browser_agent.py` - метод `search_inn_in_storage()` (строки 621-690)

**Проблемный код:**
```python
# В search_inn_comprehensive() - нет фильтрации при выборе результата
storage_results = await self.search_inn_in_storage()
if storage_results:
    result = storage_results[0]  # Берет первый результат без проверки!
    return {
        "inn": result["inn"],
        "context": f"Found in {result['source']}, key: {result.get('key', 'unknown')}",
        ...
    }
```

**Последствия:**
- Агент находит неправильные ИНН из метрик
- Нет приоритизации источников (storage может быть менее надежным)
- Нет проверки контекста

**Рекомендации:**
1. Добавить фильтрацию ключей в `search_inn_in_storage()`:
   ```python
   # Исключать ключи метрик
   tracking_prefixes = ['_ym', '_ga', 'gtag', '_gid', '_fbp', '_fbc']
   if any(key.startswith(prefix) for prefix in tracking_prefixes):
       continue  # Пропустить этот ключ
   ```
2. Добавить проверку контекста значения:
   ```python
   # Проверять, что значение содержит контекстные слова
   context_words = ['инн', 'реквизиты', 'компания', 'организация']
   if not any(word in value.lower() for word in context_words):
       continue  # Пропустить, если нет контекста
   ```
3. Изменить приоритизацию в `search_inn_comprehensive()`:
   - Сначала DOM (видимые элементы)
   - Потом HTML
   - Storage только если ничего не найдено в DOM/HTML
   - При выборе из storage - проверять ключ и контекст

### 4. Проблема с валидацией

**Описание:** Валидация ИНН проверяет только формат (10-12 цифр), но не контекст.

**Детали:**
- Функция `validate_inn()` в `ollama_inn_extractor/app/extractors/inn_extractor.py` проверяет только формат
- Нет проверки, что ИНН найден в правильном контексте (реквизиты, контакты)
- Нет проверки источника (DOM vs storage)
- Нет проверки ключа localStorage (может быть метрика)

**Место в коде:**
- `ollama_inn_extractor/app/extractors/inn_extractor.py` - функция `validate_inn()` (строки 147-166)

**Проблемный код:**
```python
def validate_inn(inn: str) -> bool:
    """Validate INN format."""
    if not inn:
        return False
    inn = inn.strip()
    if not inn.isdigit():
        return False
    return len(inn) in [10, 12]  # Только проверка формата!
```

**Последствия:**
- Агент принимает любые 10-12 цифр за ИНН
- Нет проверки контекста (метрики, трекинг, случайные числа)
- Нет проверки источника

**Рекомендации:**
1. Расширить функцию `validate_inn()`:
   ```python
   def validate_inn(inn: str, context: str = None, source: str = None, key: str = None) -> bool:
       # Проверка формата
       if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
           return False
       
       # Проверка источника
       if source == 'storage' and key:
           # Исключать ключи метрик
           tracking_prefixes = ['_ym', '_ga', 'gtag', '_gid', '_fbp', '_fbc']
           if any(key.startswith(prefix) for prefix in tracking_prefixes):
               return False
       
       # Проверка контекста (если есть)
       if context:
           context_lower = context.lower()
           # Должен содержать контекстные слова
           context_words = ['инн', 'реквизиты', 'компания', 'организация', 'налог']
           if not any(word in context_lower for word in context_words):
               # Если нет контекста, но есть подозрительные слова - отклонить
               suspicious_words = ['tracking', 'analytics', 'metric', 'session', 'cookie']
               if any(word in context_lower for word in suspicious_words):
                   return False
       
       return True
   ```
2. Использовать расширенную валидацию во всех местах поиска ИНН

## Выводы

### Критические проблемы
1. ✅ **Неправильный ИНН найден** - агент нашел ID метрики вместо ИНН компании
2. ✅ **Отсутствие фильтрации** - нет проверки ключей метрик в localStorage
3. ✅ **Слабая валидация** - проверяется только формат, без контекста

### Проблемы производительности
1. ✅ **Медленная работа** - 43 секунды из-за таймаута AI (30 секунд)

### Статус задачи
**❌ ЗАДАЧА НЕ ВЫПОЛНЕНА**

Агент нашел неправильный ИНН (ID метрики), а не ИНН компании. Правильный ИНН не найден.

## Рекомендации по исправлению

### Приоритет 1 (Критично)
1. Добавить фильтрацию ключей метрик в `search_inn_in_storage()`
2. Расширить валидацию ИНН с проверкой контекста и источника
3. Изменить приоритизацию источников (DOM > HTML > storage)

### Приоритет 2 (Важно)
1. Уменьшить таймаут AI до 10-15 секунд
2. Улучшить fallback логику (раньше переходить на fallback)

### Приоритет 3 (Желательно)
1. Добавить логирование всех найденных ИНН с их источниками
2. Добавить проверку контекста перед возвратом результата
3. Добавить метрики производительности

## Файлы для исправления

1. `ollama_inn_extractor/app/agents/browser_agent.py`
   - Метод `search_inn_in_storage()` - добавить фильтрацию ключей
   - Метод `search_inn_comprehensive()` - изменить приоритизацию

2. `ollama_inn_extractor/app/extractors/inn_extractor.py`
   - Функция `validate_inn()` - расширить валидацию

3. `ollama_inn_extractor/app/agents/interactive_inn_finder.py`
   - Уменьшить таймаут AI

---

**Примечание:** Этот отчет создан для фиксации проблем. Код НЕ исправлен - агент должен сам найти правильный ИНН.



