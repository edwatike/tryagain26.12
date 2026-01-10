# Карта проекта B2B Platform

**Дата создания:** 2025-12-29  
**Цель:** Предоставить полное описание структуры проекта, всех директорий и ключевых файлов для быстрого понимания архитектуры.

## Общая структура проекта

```
tryagain/
├── backend/              # Backend сервис (FastAPI)
├── frontend/             # Frontend сервис (Next.js)
│   └── moderator-dashboard-ui/  # Основной Frontend приложение
├── parser_service/       # Parser Service (Python, Chrome CDP)
├── docs/                 # Документация проекта
│   └── archive/          # Архивная документация
├── scripts/              # Скрипты автоматизации и запуска
├── logs/                 # Логи сервисов
├── temp/                 # Временные файлы и эксперименты
└── migrations/           # Миграции БД (в backend/migrations)
```

## Backend (FastAPI)

### Структура директорий

```
backend/
├── app/                  # Основной код приложения
│   ├── main.py          # Точка входа FastAPI приложения
│   ├── config.py        # Конфигурация (настройки, переменные окружения)
│   ├── transport/       # HTTP слой (роутеры, схемы)
│   ├── usecases/        # Бизнес-логика (чистая логика без HTTP)
│   ├── adapters/        # Внешние сервисы (Parser Service, Checko, Ollama)
│   └── db/              # Работа с БД (модели, репозитории, сессии)
├── migrations/          # SQL миграции БД
├── tests/               # Тесты
└── requirements.txt     # Python зависимости
```

### Ключевые файлы Backend

#### `app/main.py`
**Назначение:** Точка входа FastAPI приложения  
**Содержит:**
- Создание FastAPI приложения
- Настройка CORS
- Регистрация роутеров
- Обработка ошибок
- Логирование

**Роутеры:**
- `health` - проверка работоспособности
- `moderator_suppliers` - управление поставщиками
- `keywords` - управление ключевыми словами
- `blacklist` - управление черным списком
- `parsing` - запуск парсинга
- `parsing_runs` - история парсинга и логи
- `domains_queue` - очередь доменов
- `attachments` - вложения

#### `app/transport/routers/`
**Назначение:** FastAPI endpoints (ТОЛЬКО маршрутизация)  
**Файлы:**
- `parsing.py` - запуск парсинга (`POST /parsing/start`)
- `parsing_runs.py` - история парсинга, логи (`GET /parsing/runs`, `GET /parsing/runs/{run_id}/logs`)
- `domains_queue.py` - очередь доменов (`GET /domains/queue`)
- `keywords.py` - ключевые слова (`GET /keywords`, `POST /keywords`)
- `blacklist.py` - черный список (`GET /moderator/blacklist`, `POST /moderator/blacklist`)
- `moderator_suppliers.py` - поставщики (`GET /moderator/suppliers`, `POST /moderator/suppliers`)
- `health.py` - проверка работоспособности (`GET /health`)

**Правило:** Роутеры НЕ должны содержать бизнес-логику, только маршрутизацию.

#### `app/transport/schemas/`
**Назначение:** Pydantic схемы (DTO)  
**Файлы:**
- `parsing.py` - схемы для парсинга
- `domain.py` - схемы для доменов
- `keywords.py` - схемы для ключевых слов
- `blacklist.py` - схемы для черного списка
- `moderator_suppliers.py` - схемы для поставщиков
- `common.py` - общие схемы

**Правило:** Все схемы используют camelCase для JSON сериализации.

#### `app/usecases/`
**Назначение:** Бизнес-логика (чистая логика без HTTP)  
**Файлы:**
- `start_parsing.py` - запуск парсинга (критически важно!)
- `get_parsing_status.py` - получение статуса парсинга
- `get_parsing_run.py` - получение запуска парсинга
- `list_parsing_runs.py` - список запусков парсинга
- `delete_parsing_run.py` - удаление запуска парсинга
- `list_domains_queue.py` - список доменов в очереди
- `list_keywords.py` - список ключевых слов
- `create_keyword.py` - создание ключевого слова
- `add_to_blacklist.py` - добавление в черный список
- `list_blacklist.py` - список черного списка
- `create_moderator_supplier.py` - создание поставщика
- `list_moderator_suppliers.py` - список поставщиков

**Правило:** Usecases НЕ должны знать о HTTP, только о бизнес-логике.

#### `app/adapters/`
**Назначение:** Внешние сервисы и адаптеры  
**Файлы:**
- `parser_client.py` - клиент для Parser Service (HTTP)
- `db/` - работа с БД
  - `models.py` - SQLAlchemy модели
  - `repositories.py` - репозитории для работы с БД
  - `session.py` - сессии БД
  - `base_repository.py` - базовый репозиторий

**Правило:** Адаптеры изолируют внешние зависимости.

#### `app/db/`
**Назначение:** Работа с базой данных  
**Файлы:**
- `models.py` - SQLAlchemy модели (таблицы БД)
- `repositories.py` - репозитории для CRUD операций
- `session.py` - создание сессий БД
- `base_repository.py` - базовый репозиторий с общими методами

**Модели:**
- `ParsingRun` - запуски парсинга
- `DomainQueue` - очередь доменов
- `Keyword` - ключевые слова
- `ModeratorSupplier` - поставщики
- `BlacklistEntry` - черный список

#### `migrations/`
**Назначение:** SQL миграции БД  
**Файлы:**
- `001_initial.sql` - начальная миграция
- `007_add_source_to_domains_queue.sql` - добавление поля source
- И другие миграции

**Правило:** Все изменения схемы БД должны быть через миграции.

## Frontend (Next.js)

### Структура директорий

```
frontend/moderator-dashboard-ui/
├── app/                  # Next.js App Router страницы
│   ├── page.tsx         # Главная страница (Dashboard)
│   ├── layout.tsx        # Общий layout
│   ├── manual-parsing/   # Страница ручного парсинга
│   ├── parsing-runs/    # Страницы истории парсинга
│   │   ├── page.tsx     # Список запусков
│   │   └── [runId]/     # Детали запуска
│   ├── keywords/         # Страница ключевых слов
│   ├── suppliers/        # Страницы поставщиков
│   └── blacklist/        # Страница черного списка
├── components/           # React компоненты
│   ├── ui/              # Shadcn UI компоненты
│   ├── navigation.tsx   # Навигация
│   └── ...
├── lib/                  # Утилиты и API клиент
│   ├── api.ts           # API клиент (все HTTP запросы)
│   ├── types.ts         # TypeScript типы
│   ├── utils-domain.ts  # Утилиты для работы с доменами
│   ├── cache.ts         # Кэширование данных
│   └── utils.ts         # Общие утилиты
└── package.json         # Зависимости
```

### Ключевые файлы Frontend

#### `app/page.tsx`
**Назначение:** Главная страница (Dashboard)  
**Содержит:**
- Форма запуска парсинга
- Прогрессбар парсинга в реальном времени
- Список последних найденных доменов
- Метрики (количество ключевых слов, поставщиков, доменов)
- Polling для обновления статуса парсинга

**Ключевые функции:**
- `handleStartParsing()` - запуск парсинга
- Polling для статуса парсинга
- Отображение прогресса и последних доменов

#### `app/parsing-runs/[runId]/page.tsx`
**Назначение:** Страница деталей запуска парсинга  
**Содержит:**
- Информация о запуске парсинга
- Список доменов с группировкой
- Фильтрация blacklist
- Отображение статусов (Поставщик/Реселлер)
- Отображение источников (Google/Яндекс) для доменов
- Логи парсинга в реальном времени
- Добавление в blacklist
- Создание поставщиков

**Ключевые функции:**
- `loadData()` - загрузка данных (run, domains, logs, suppliers, blacklist)
- `groupByDomain()` - группировка доменов
- `collectDomainSources()` - определение источников для доменов
- Polling для логов парсинга

**Критические точки интеграции:**
- Фильтрация blacklist (ПЕРЕД группировкой)
- Определение источников (использует parsing_logs)
- Отображение статусов поставщиков

#### `app/keywords/page.tsx`
**Назначение:** Страница ключевых слов  
**Содержит:**
- Список ключевых слов с двойным accordion
- Группировка доменов по ключевым словам
- Фильтрация blacklist
- Отображение статусов поставщиков

**Ключевые функции:**
- `loadKeywords()` - загрузка списка ключевых слов
- `loadUrlsForKeyword()` - ленивая загрузка URL для ключевого слова
- Группировка доменов с фильтрацией blacklist

#### `app/manual-parsing/page.tsx`
**Назначение:** Страница ручного парсинга  
**Содержит:**
- Форма для запуска парсинга
- Выбор источника (Google/Yandex/Both)
- Выбор глубины парсинга

#### `lib/api.ts`
**Назначение:** API клиент (все HTTP запросы)  
**Содержит:**
- Все функции для работы с API
- `apiFetch()` - базовая функция для запросов
- `apiFetchWithRetry()` - запросы с retry механизмом
- Функции для всех endpoints:
  - `startParsing()` - запуск парсинга
  - `getParsingStatus()` - статус парсинга
  - `getParsingRun()` - получение запуска
  - `getParsingLogs()` - получение логов парсинга
  - `getDomainsQueue()` - очередь доменов
  - `getKeywords()` - ключевые слова
  - `getBlacklist()` - черный список
  - `addToBlacklist()` - добавление в blacklist
  - `getSuppliers()` - поставщики
  - И другие

**Правило:** Все HTTP запросы идут через этот файл, нельзя вызывать `fetch()` напрямую из компонентов.

#### `lib/types.ts`
**Назначение:** TypeScript типы  
**Содержит:**
- Все типы данных для работы с API
- `ParsingRunDTO` - запуск парсинга
- `DomainQueueEntryDTO` - запись в очереди доменов
- `ParsingDomainGroup` - группа доменов
- `SupplierDTO` - поставщик
- `BlacklistEntryDTO` - запись в черном списке
- `KeywordDTO` - ключевое слово
- `ParsingLogsDTO` - логи парсинга

**Правило:** Все типы должны соответствовать Pydantic схемам Backend.

#### `lib/utils-domain.ts`
**Назначение:** Утилиты для работы с доменами  
**Содержит:**
- `extractRootDomain()` - извлечение корневого домена
- `normalizeUrl()` - нормализация URL для сравнения
- `groupByDomain()` - группировка доменов
- `collectDomainSources()` - определение источников для доменов (Google/Яндекс)

**Критически важно:** Эти функции используются в нескольких местах, изменения должны быть согласованы.

#### `lib/cache.ts`
**Назначение:** Кэширование данных  
**Содержит:**
- `getCachedSuppliers()` - получение кэшированных поставщиков
- `setCachedSuppliers()` - сохранение поставщиков в кэш
- `getCachedBlacklist()` - получение кэшированного blacklist
- `setCachedBlacklist()` - сохранение blacklist в кэш
- `invalidateSuppliersCache()` - инвалидация кэша поставщиков
- `invalidateBlacklistCache()` - инвалидация кэша blacklist

**Правило:** Blacklist всегда загружается свежим при отображении результатов, кэш используется только для оптимизации.

#### `components/ui/`
**Назначение:** Shadcn UI компоненты  
**Содержит:**
- `accordion.tsx` - аккордеон
- `badge.tsx` - бейджи
- `button.tsx` - кнопки
- `card.tsx` - карточки
- `dialog.tsx` - диалоги
- `input.tsx` - поля ввода
- `select.tsx` - селекты
- И другие

## Parser Service

### Структура директорий

```
parser_service/
├── api.py               # FastAPI приложение Parser Service
├── run_api.py          # Скрипт запуска API
├── src/                # Основной код
│   ├── parser.py      # Основной класс Parser
│   ├── engines.py     # Классы поисковых движков (GoogleEngine, YandexEngine)
│   ├── cdp_client.py  # Клиент для Chrome CDP
│   ├── human_behavior.py  # Эмуляция человеческого поведения
│   ├── config.py      # Конфигурация
│   └── utils.py       # Утилиты
└── requirements.txt    # Python зависимости
```

### Ключевые файлы Parser Service

#### `api.py`
**Назначение:** FastAPI приложение Parser Service  
**Содержит:**
- `POST /parse` - endpoint для запуска парсинга
- Обработка запросов парсинга
- Управление Chrome CDP
- Отправка логов парсинга на Backend

**Ключевые функции:**
- `parse_keyword()` - обработка запроса парсинга
- `run_parsing_in_thread()` - запуск парсинга в отдельном потоке (Windows)
- `send_logs_periodically()` - периодическая отправка логов

#### `src/parser.py`
**Назначение:** Основной класс Parser  
**Содержит:**
- `Parser` - основной класс для парсинга
- `parse_keyword()` - парсинг ключевого слова
- `_send_parsing_logs()` - отправка логов на Backend
- Управление браузером и страницами

**Ключевые методы:**
- `parse_keyword()` - основной метод парсинга
- `_send_parsing_logs()` - отправка логов каждые 2.5 секунды
- `close()` - закрытие браузера

#### `src/engines.py`
**Назначение:** Классы поисковых движков  
**Содержит:**
- `SearchEngine` - базовый класс
- `GoogleEngine` - парсинг Google
- `YandexEngine` - парсинг Yandex

**Ключевые методы:**
- `parse()` - парсинг результатов поиска
- Обновление `parsing_logs` при нахождении ссылок
- Отслеживание источников для каждого URL

**Критически важно:**
- Обновление `parsing_logs` с первой найденной ссылки
- Отслеживание источников (`collected_links[url].add("google")` или `"yandex"`)

## Документация

### Структура документации

```
docs/
├── MASTER_INSTRUCTION.md           # Главная инструкция (обязательна к прочтению)
├── TROUBLESHOOTING.md              # Библия ошибок и решений
├── CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md  # Критические точки интеграции
├── PROJECT_SPECIFICATION.md        # Детальная спецификация API
├── PROJECT_MAP.md                  # Карта проекта (этот файл)
├── archive/                        # Архивная документация
│   ├── QUICK_START.md              # Быстрый старт (архив)
│   ├── CREATE_ENV.md               # Создание .env (архив)
│   ├── DATABASE_SETUP_GUIDE.md     # Настройка БД (архив)
│   ├── START_HERE.md               # Точка входа (архив)
│   ├── APPLY_MIGRATIONS.md         # Применение миграций (архив)
│   ├── README_START.md             # Запуск в 2 клика (архив)
│   ├── FIXED_ISSUES.md             # Исправленные проблемы (архив)
│   ├── LAUNCH_STATUS.md            # Статус запуска (архив)
│   └── RUN_STATUS.md               # Статус запуска (архив)
└── ...                             # Другие документы
```

### Архивная документация

**Расположение:** `docs/archive/`

**Содержит:**
- Устаревшие файлы запуска и настройки
- Исторические статусные файлы
- Старые версии инструкций

**Примечание:** Актуальная информация находится в `docs/MASTER_INSTRUCTION.md`. Архивные файлы сохранены для истории.

### Ключевые документы

#### `DOCUMENTATION_INDEX.md`
**Назначение:** Главная точка входа в документацию  
**Содержит:**
- Структура документации
- Порядок чтения документов
- Чеклист для нового чата

#### `PROJECT_SPECIFICATION.md`
**Назначение:** Спецификация проекта  
**Содержит:**
- Описание всех рабочих связок Backend-Frontend
- Endpoint'ы и функции
- Команды для проверки работоспособности
- Примеры запросов/ответов

#### `TROUBLESHOOTING.md`
**Назначение:** Библия ошибок и решений  
**Содержит:**
- Все ошибки и их решения
- ОБЯЗАТЕЛЬНЫЕ ПРОВЕРКИ перед диагностикой
- Чеклист диагностики
- Рекомендации для быстрой диагностики

#### `CRITICAL_INTEGRATION_POINTS.md`
**Назначение:** Критические точки интеграции  
**Содержит:**
- Описание всех функциональностей, используемых в нескольких местах
- Места использования
- Правила реализации
- Чеклисты проверки

#### `SOURCE_DETERMINATION_FLOW.md`
**Назначение:** Поток данных для определения источников  
**Содержит:**
- Полный поток данных от парсера до фронтенда
- Диаграммы
- Примеры работы
- Проблемы и решения

## Скрипты автоматизации

### Структура скриптов

```
scripts/
├── PowerShell скрипты (.ps1):
│   ├── quick-check.ps1              # Быстрая проверка всех сервисов
│   ├── monitor-services.ps1         # Мониторинг сервисов
│   ├── validate-migration.ps1       # Валидация миграций
│   ├── check-sequences-after-migration.ps1  # Проверка последовательностей
│   └── start-all-services-single-window.ps1  # Запуск всех сервисов
│
└── Batch скрипты (.bat):
    ├── start-backend.bat            # Запуск Backend
    ├── start-frontend.bat           # Запуск Frontend
    ├── start-parser.bat              # Запуск Parser Service
    ├── start-chrome.bat              # Запуск Chrome CDP
    ├── setup-database.bat           # Настройка базы данных
    ├── start-all-tabby.bat          # Запуск всех сервисов (один клик)
    └── stop-all.bat                 # Остановка всех сервисов
```

### Ключевые скрипты

#### `quick-check.ps1`
**Назначение:** Быстрая проверка всех сервисов  
**Использование:**
```powershell
.\scripts\quick-check.ps1 all
```

**Проверяет:**
- Импорты Backend
- Линтер Frontend
- Health endpoints всех сервисов

#### `monitor-services.ps1`
**Назначение:** Мониторинг состояния сервисов  
**Использование:**
```powershell
.\scripts\monitor-services.ps1
```

**Проверяет:**
- Состояние всех сервисов
- Порты и процессы
- Логи последних ошибок

## Зависимости между модулями

### Backend → Parser Service
- `app/adapters/parser_client.py` → HTTP запросы к Parser Service
- `app/usecases/start_parsing.py` → вызов Parser Service для парсинга

### Frontend → Backend
- `lib/api.ts` → все HTTP запросы к Backend
- Все страницы → используют функции из `lib/api.ts`

### Parser Service → Backend
- `src/parser.py` → отправка логов на Backend (`PUT /parsing/runs/{run_id}/logs`)

### Frontend внутренние зависимости
- Все страницы → `lib/api.ts` (API запросы)
- Все страницы → `lib/types.ts` (типы)
- Страницы с доменами → `lib/utils-domain.ts` (утилиты для доменов)
- Страницы с кэшированием → `lib/cache.ts` (кэширование)

## Критические точки интеграции

### 1. Определение источников для доменов (Google/Яндекс)
**Файлы:**
- `frontend/lib/utils-domain.ts` - функция `collectDomainSources()`
- `frontend/app/parsing-runs/[runId]/page.tsx` - использование функции
- `frontend/app/page.tsx` - отображение источников

**Документация:** `docs/SOURCE_DETERMINATION_FLOW.md`, `docs/CRITICAL_INTEGRATION_POINTS.md`

### 2. Фильтрация blacklist
**Файлы:**
- `frontend/app/parsing-runs/[runId]/page.tsx` - фильтрация перед группировкой
- `frontend/app/keywords/page.tsx` - фильтрация при загрузке URL

**Документация:** `docs/CRITICAL_INTEGRATION_POINTS.md`

### 3. Группировка доменов
**Файлы:**
- `frontend/lib/utils-domain.ts` - функция `groupByDomain()`
- Используется в нескольких страницах

**Документация:** `docs/CRITICAL_INTEGRATION_POINTS.md`

### 4. Отображение статусов поставщиков
**Файлы:**
- `frontend/app/parsing-runs/[runId]/page.tsx` - отображение статусов
- `frontend/app/keywords/page.tsx` - отображение статусов

**Документация:** `docs/CRITICAL_INTEGRATION_POINTS.md`

## Порты и сервисы

### Порты
- **Backend:** `8000` (http://127.0.0.1:8000)
- **Frontend:** `3000` (http://localhost:3000)
- **Parser Service:** `9003` (http://127.0.0.1:9003)
- **Chrome CDP:** `9222` (http://127.0.0.1:9222)

### Health endpoints
- Backend: `GET http://127.0.0.1:8000/health`
- Parser Service: `GET http://127.0.0.1:9003/health`
- Chrome CDP: `GET http://127.0.0.1:9222/json/version`

## База данных

### Таблицы
- `parsing_runs` - запуски парсинга (содержит `process_log` с `parsing_logs`)
- `domains_queue` - очередь доменов (содержит `source`: "google", "yandex", или "both")
- `keywords` - ключевые слова
- `moderator_suppliers` - поставщики
- `moderator_blacklist` - черный список

### Миграции
- Расположение: `backend/migrations/`
- Применение: через SQL скрипты
- Валидация: `scripts/validate-migration.ps1`

## Временные файлы

### `temp/` и `temp/experiments/`

**Назначение:** Временные файлы, эксперименты, старые версии интерфейса

**Структура:**
```
temp/
├── backend/              # Временные скрипты для Backend
├── experiments/          # Экспериментальные версии и дизайн-проекты
│   ├── moderator-dashboardNEW/        # Старая версия frontend
│   ├── supplier-card-design/          # Дизайн-проект карточки поставщика
│   └── supplier-moderation-dashboard/  # Старая версия dashboard
└── temp_start_all_output.txt  # Временные файлы вывода
```

**Правило:** 
- Все временные файлы, debug-код, проверки гипотез, старые версии интерфейса должны быть только в `temp/` или `temp/experiments/`
- Запрещено создавать тестовые файлы в `backend/app/**`, `frontend/moderator-dashboard-ui/**`, `parser_service/src/**`
- Если эксперимент стал постоянной частью системы - перенести из `temp/` в нужный рабочий каталог
**Назначение:** Временные файлы и эксперименты  
**Содержит:**
- Тестовые скрипты
- Шаблоны для документирования
- Экспериментальные изменения

**Правило:** Все временные файлы должны быть в `temp/`, не в корне проекта.

## Логи

### `logs/`
**Назначение:** Логи сервисов  
**Содержит:**
- `Backend-*.log` - логи Backend
- `Frontend-*.log` - логи Frontend
- `Parser Service-*.log` - логи Parser Service

**Использование:**
- Для диагностики проблем
- Проверка последних ошибок
- Мониторинг работы сервисов

## Связанные документы

- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - главная точка входа
- [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) - спецификация проекта
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - библия ошибок
- [CRITICAL_INTEGRATION_POINTS.md](CRITICAL_INTEGRATION_POINTS.md) - критические точки
- [SOURCE_DETERMINATION_FLOW.md](SOURCE_DETERMINATION_FLOW.md) - поток данных
- [AI_AGENT_IMPROVEMENTS.md](AI_AGENT_IMPROVEMENTS.md) - рекомендации по улучшению работы AI




