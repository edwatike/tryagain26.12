# Применение миграций БД

## Проблема
Автоматическое применение миграций через Python не работает из-за проблем с подключением на Windows.

## Решение

### Вариант 1: Через pgAdmin (рекомендуется)

1. Откройте pgAdmin
2. Подключитесь к серверу PostgreSQL
3. Выберите базу данных `postgres`
4. Откройте Query Tool (Правка -> Query Tool)
5. Откройте файл `backend/migrations/001_initial_schema.sql`
6. Скопируйте весь SQL и выполните (F5)

### Вариант 2: Через командную строку PostgreSQL

```powershell
cd D:\tryagain\backend\migrations
psql -U postgres -d postgres -h localhost -f 001_initial_schema.sql
```

При запросе пароля введите пароль из `backend/.env` (по умолчанию `postgres`)

### Вариант 3: Через DBeaver или другой SQL клиент

1. Подключитесь к PostgreSQL
2. Выберите базу `postgres`
3. Выполните SQL из `backend/migrations/001_initial_schema.sql`

## Проверка

После применения миграций проверьте:

```powershell
# Проверка через API
Invoke-WebRequest -Uri "http://127.0.0.1:8000/moderator/suppliers?limit=1"
```

Должен вернуться статус 200 с пустым списком suppliers, а не ошибка 500.

## Данные подключения

Из `backend/app/config.py`:
- Host: localhost
- Port: 5432
- Database: postgres (или из DATABASE_URL)
- User: postgres (или из DATABASE_URL)
- Password: из DATABASE_URL в backend/.env

