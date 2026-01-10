⚠️ **АРХИВ. Актуальная версия: см. `docs/MASTER_INSTRUCTION.md`**

# 🚀 Запуск B2B Platform в 2 клика

## Быстрый старт

### Шаг 1: Настройка базы данных (один раз)

Если у вас уже есть PostgreSQL база данных:

1. Откройте `backend/.env` и укажите ваши данные БД:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```

2. Примените миграции к вашей БД:
   ```powershell
   .\setup-database.bat
   ```
   
   Или вручную:
   ```powershell
   psql -U postgres -d your_database -f backend\migrations\001_initial_schema.sql
   ```

### Шаг 2: Запуск всех сервисов

**Просто запустите:**
```powershell
.\start-all.bat
```

Это запустит:
- ✅ Chrome CDP (порт 9222)
- ✅ Parser Service (порт 9003)
- ✅ Backend API (порт 8000)
- ✅ Frontend (порт 3000)

Все сервисы откроются в отдельных окнах.

### Шаг 3: Откройте в браузере

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://127.0.0.1:8000/docs

## Остановка всех сервисов

```powershell
.\stop-all.bat
```

## Настройка переменных окружения

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
PARSER_SERVICE_URL=http://127.0.0.1:9003
ENV=development
LOG_LEVEL=INFO
```

### Frontend (`frontend/moderator-dashboard-ui/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_CHECKO_API_KEY=your_checko_api_key_here
```

## Требования

- Python 3.12+
- Node.js 18+
- PostgreSQL (любая версия, база должна существовать)
- Google Chrome

## Устранение проблем

### Порт занят
```powershell
# Найти процесс
netstat -ano | findstr :8000
# Остановить
taskkill /PID <PID> /F
```

### База данных не найдена
Убедитесь, что:
1. PostgreSQL запущен
2. База данных существует
3. Правильные credentials в `backend/.env`

### Chrome не запускается
Проверьте путь к Chrome в `start-all.bat`:
```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe"
```

## Что дальше?

После запуска:
1. Откройте http://localhost:3000
2. Создайте первого поставщика
3. Добавьте ключевые слова
4. Запустите парсинг

