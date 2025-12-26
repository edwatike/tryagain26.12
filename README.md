# B2B Platform

Система для автоматизации поиска, парсинга и модерации поставщиков с интеграцией Checko API.

## Технологический стек

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python), SQLAlchemy 2.0, PostgreSQL
- **Parser Service**: FastAPI, Playwright, Chrome CDP
- **База данных**: PostgreSQL 15

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

## Быстрый старт (2 клика!)

### Вариант 1: Автоматический запуск (рекомендуется)

1. **Настройте подключение к БД** (один раз):
   - Откройте `backend/.env` и укажите вашу БД:
     ```
     DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
     ```
   - Примените миграции:
     ```powershell
     .\setup-database.bat
     ```

2. **Запустите всё одной командой:**
   ```powershell
   .\start-all.bat
   ```

Готово! Все сервисы запущены. Откройте http://localhost:3000

### Вариант 2: Ручной запуск

### Требования

- Python 3.12+
- Node.js 18+
- PostgreSQL (любая версия, база должна существовать)
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
# Linux/Mac:
google-chrome --remote-debugging-port=9222 --headless
# Windows:
chrome.exe --remote-debugging-port=9222 --headless

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

## Документация

Полная документация проекта находится в `D:\b2b\DOCsV1`.

## Лицензия

MIT

