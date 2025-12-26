# Инструкция по настройке базы данных

## Шаг 1: Создание базы данных

Если у вас еще нет базы данных PostgreSQL, создайте её одним из способов:

### Вариант 1: Через psql

```powershell
psql -U postgres
CREATE DATABASE b2b_dev;
\q
```

### Вариант 2: Через createdb

```powershell
createdb -U postgres b2b_dev
```

### Вариант 3: Использовать существующую базу

Если у вас уже есть база данных, просто используйте её имя в настройках.

## Шаг 2: Настройка DATABASE_URL в backend/.env

Откройте файл `backend/.env` и обновите строку `DATABASE_URL` с вашими данными:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
```

Примеры:

```env
# Локальная база, стандартные настройки
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres

# Локальная база с другим именем
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/b2b_dev

# Удаленная база
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/b2b_prod
```

**Важно:** 
- Замените `USER`, `PASSWORD`, `HOST`, `PORT`, `DATABASE` на ваши реальные значения
- Используйте формат `postgresql+asyncpg://` (не просто `postgresql://`)

## Шаг 3: Применение миграций

### Автоматический способ (рекомендуется)

```powershell
.\setup-database.bat
```

Скрипт попросит ввести:
- Имя базы данных
- Пользователя БД
- Пароль
- Хост
- Порт

После этого миграции будут применены автоматически.

### Ручной способ

```powershell
psql -U postgres -d your_database_name -f backend\migrations\001_initial_schema.sql
```

Или если база на другом хосте:

```powershell
psql -h localhost -p 5432 -U postgres -d b2b_dev -f backend\migrations\001_initial_schema.sql
```

## Шаг 4: Проверка миграций

Проверьте, что таблицы созданы:

```powershell
psql -U postgres -d your_database_name -c "\dt"
```

Должны быть созданы следующие таблицы:
- `moderator_suppliers`
- `keywords`
- `supplier_keywords`
- `blacklist`
- `parsing_runs`
- `domains_queue`

## Шаг 5: Проверка подключения

После настройки запустите Backend:

```powershell
.\start-backend.bat
```

Проверьте, что нет ошибок подключения к БД. Если есть ошибки, проверьте:
1. PostgreSQL запущен
2. DATABASE_URL в `.env` правильный
3. Пользователь БД имеет права на базу данных
4. Миграции применены

## Устранение проблем

### Ошибка: "database does not exist"

Создайте базу данных (см. Шаг 1).

### Ошибка: "password authentication failed"

Проверьте правильность пароля в `DATABASE_URL`.

### Ошибка: "connection refused"

Проверьте:
- PostgreSQL запущен
- Хост и порт в `DATABASE_URL` правильные
- Файрвол не блокирует подключение

### Ошибка: "relation does not exist"

Примените миграции (см. Шаг 3).

### Ошибка: "permission denied"

Убедитесь, что пользователь БД имеет права на создание таблиц и работу с базой данных.

## Дополнительная информация

- Файл миграции: `backend/migrations/001_initial_schema.sql`
- Скрипт настройки: `setup-database.bat`
- Конфигурация: `backend/.env`

