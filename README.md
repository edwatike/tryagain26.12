# B2B Platform

## 📚 Документация

**⚠️ ВАЖНО: Перед началом работы изучи документацию!**

- **Главная точка входа**: [`docs/DOCUMENTATION_INDEX.md`](docs/DOCUMENTATION_INDEX.md) - **НАЧНИ ОТСЮДА!**
- **Библия ошибок**: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - все ошибки и решения (НЕПРИКОСНОВЕННАЯ!)
- **Правила работы AI**: [`.cursorrules`](.cursorrules) - правила для AI-агента
- **Навигация по документации**: [`docs/README.md`](docs/README.md)

**При возникновении ошибки:**
1. СНАЧАЛА проверь [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
2. Если решения нет - реши и ОБЯЗАТЕЛЬНО задокументируй

---

# B2B Platform

Система для автоматизации поиска, парсинга и модерации поставщиков с интеграцией Checko API.

## Технологический стек

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python), SQLAlchemy 2.0, PostgreSQL
- **Parser Service**: FastAPI, Playwright, Chrome CDP
- **База данных**: PostgreSQL 15 (используется база `b2bplatform`)

## Структура проекта

```
b2b-platform/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── adapters/          # Адаптеры к внешним системам
│   │   ├── domain/            # Доменная логика
│   │   ├── transport/         # HTTP слой (роутеры, схемы)
│   │   ├── usecases/          # Бизнес-логика
│   │   ├── config.py
│   │   └── main.py
│   ├── migrations/            # SQL миграции
│   ├── tests/                 # Тесты
│   └── requirements.txt
│
├── frontend/
│   └── moderator-dashboard-ui/  # Next.js Frontend
│       ├── app/                 # App Router
│       ├── components/         # React компоненты
│       ├── lib/                # Утилиты
│       └── package.json
│
└── parser_service/            # Parser Service
    ├── src/
    ├── api.py
    ├── run_api.py
    └── requirements.txt
```

## Быстрый старт (1 клик!)

### ⚡ Автоматический запуск (рекомендуется)

**⚠️ ВАЖНО: Теперь все сервисы запускаются в одном окне терминала с цветным логированием!**

1. **Настройте подключение к БД** (один раз):
   - ⚠️ **ВАЖНО:** Используется база данных `b2bplatform` (пароль: `Jnvnszoe5971312059001`)
   - Откройте `backend/.env` и установите:
     ```
     DATABASE_URL=postgresql+asyncpg://postgres:Jnvnszoe5971312059001@localhost:5432/b2bplatform
     ```
   - Примените миграции:
     ```powershell
     $env:PGPASSWORD="Jnvnszoe5971312059001"
     psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\001_initial_schema.sql
     psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\002_audit_log.sql
     ```
   - Подробности: см. `docs/DATABASE_CONFIG.md`

2. **Запустите всё одной командой:**
   ```batch
   start-all-tabby.bat
   ```

**Готово!** Все сервисы запущены в одном окне терминала с:
- ✅ Цветным логированием (ошибки - красным, успех - зеленым)
- ✅ Мониторингом в реальном времени
- ✅ Автоматическими health checks
- ✅ Оптимизированной нагрузкой на систему

**Откройте:** http://localhost:3000

**📖 Подробная документация:** [`docs/SERVER_STARTUP.md`](docs/SERVER_STARTUP.md)

### Вариант 2: Ручной запуск

### Требования

- Python 3.12+
- Node.js 18+
- PostgreSQL (любая версия, используется база `b2bplatform`)
- Google Chrome (для парсинга)

### 1. Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.\venv\Scripts\Activate.ps1  # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать базу данных
createdb b2b_dev

# Применить миграции
psql -U postgres -d b2b_dev -f migrations/001_initial_schema.sql

# Создать .env файл
cp .env.example .env
# Отредактировать .env с вашими настройками

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend/moderator-dashboard-ui

# Установить зависимости
npm install

# Создать .env.local
cp .env.local.example .env.local
# Отредактировать .env.local с вашими настройками

# Запустить dev сервер
npm run dev
```

### 3. Parser Service

```bash
cd parser_service

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.\venv\Scripts\Activate.ps1  # Windows

# Установить зависимости
pip install -r requirements.txt

# Установить браузеры для Playwright
playwright install chromium

# Создать .env файл
cp .env.example .env

# Запустить Chrome в режиме отладки (в отдельном терминале)
# Chrome запускается в видимом режиме (не headless), чтобы можно было пройти капчу вручную
# Linux/Mac:
google-chrome --remote-debugging-port=9222
# Windows:
chrome.exe --remote-debugging-port=9222

# Запустить Parser Service
python run_api.py
```

## Проверка работоспособности

1. **Frontend**: http://localhost:3000
2. **Backend API**: http://127.0.0.1:8000/health
3. **Parser Service**: http://127.0.0.1:9003/health
4. **Chrome CDP**: http://127.0.0.1:9222/json/version

## API Endpoints

### Suppliers
- `GET /moderator/suppliers` - Список поставщиков
- `GET /moderator/suppliers/{id}` - Получить поставщика
- `POST /moderator/suppliers` - Создать поставщика
- `PUT /moderator/suppliers/{id}` - Обновить поставщика
- `DELETE /moderator/suppliers/{id}` - Удалить поставщика

### Keywords
- `GET /keywords` - Список ключевых слов
- `POST /keywords` - Создать ключевое слово
- `DELETE /keywords/{id}` - Удалить ключевое слово

### Parsing
- `POST /parsing/start` - Запустить парсинг
- `GET /parsing/status/{run_id}` - Статус парсинга
- `GET /parsing/runs` - История парсинга

### Blacklist
- `GET /moderator/blacklist` - Список черного списка
- `POST /moderator/blacklist` - Добавить в черный список
- `DELETE /moderator/blacklist/{domain}` - Удалить из черного списка

## Интеграция с Checko API

Для работы с Checko API необходимо:

1. Получить API ключ на https://checko.ru/integration/api
2. Добавить ключ в `.env.local` frontend:
   ```
   NEXT_PUBLIC_CHECKO_API_KEY=your_api_key_here
   ```

## Разработка

### Backend тесты

```bash
cd backend
pytest
```

### Frontend линтинг

```bash
cd frontend/moderator-dashboard-ui
npm run lint
npm run type-check
```

### Проверка импортов (Backend)

Перед коммитом рекомендуется запустить скрипт проверки импортов `date`/`datetime`:

```bash
python temp/backend/check_imports.py
```

Скрипт проверяет все роутеры и usecases на отсутствующие импорты. Подробнее см. [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - раздел "Инструменты для профилактики ошибок".

## Документация

Полная документация проекта находится в `D:\b2b\DOCsV1`.

## Лицензия

MIT

