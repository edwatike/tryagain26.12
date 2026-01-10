⚠️ **АРХИВ. Актуальная версия: см. `docs/MASTER_INSTRUCTION.md`**

# Применение миграций БД

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Используемая база данных

**ИСПОЛЬЗУЕТСЯ ТОЛЬКО ОДНА БАЗА ДАННЫХ:**

- **Имя базы данных:** `b2bplatform`
- **Пользователь:** `postgres`
- **Пароль:** `Jnvnszoe5971312059001`
- **Хост:** `localhost`
- **Порт:** `5432`

**🚨 НЕ МЕНЯТЬ базу данных без обновления всех документов и резервного копирования!**

Подробности см. в `docs/DATABASE_CONFIG.md`

## Решение

### Вариант 1: Через pgAdmin (рекомендуется)

1. Откройте pgAdmin
2. Подключитесь к серверу PostgreSQL (пароль: `Jnvnszoe5971312059001`)
3. Выберите базу данных `b2bplatform`
4. Откройте Query Tool (Правка -> Query Tool)
5. Откройте файл `backend/migrations/001_initial_schema.sql`
6. Скопируйте весь SQL и выполните (F5)
7. Откройте файл `backend/migrations/002_audit_log.sql`
8. Скопируйте весь SQL и выполните (F5)
9. Откройте файл `backend/migrations/003_parsing_requests.sql`
10. Скопируйте весь SQL и выполните (F5)
11. Откройте файл `backend/migrations/004_fix_domains_queue_primary_key.sql`
12. Скопируйте весь SQL и выполните (F5)

### Вариант 2: Через командную строку PostgreSQL (рекомендуется)

```powershell
cd D:\tryagain
$env:PGPASSWORD="Jnvnszoe5971312059001"
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\001_initial_schema.sql
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\002_audit_log.sql
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\003_parsing_requests.sql
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\004_fix_domains_queue_primary_key.sql
```

### Вариант 3: Через DBeaver или другой SQL клиент

1. Подключитесь к PostgreSQL (пароль: `Jnvnszoe5971312059001`)
2. Выберите базу `b2bplatform`
3. Выполните SQL из `backend/migrations/001_initial_schema.sql`
4. Выполните SQL из `backend/migrations/002_audit_log.sql`

## Проверка

После применения миграций проверьте:

```powershell
# Проверка через API
Invoke-WebRequest -Uri "http://127.0.0.1:8000/moderator/suppliers?limit=1"
```

Должен вернуться статус 200 с пустым списком suppliers, а не ошибка 500.

## Данные подключения

**ИСПОЛЬЗУЕТСЯ ТОЛЬКО ОДНА БАЗА ДАННЫХ:**

- Host: localhost
- Port: 5432
- Database: **b2bplatform** (НЕ МЕНЯТЬ!)
- User: postgres
- Password: **Jnvnszoe5971312059001**

Подробности см. в `docs/DATABASE_CONFIG.md`

