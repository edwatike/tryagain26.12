# FAQ: Работа с последовательностями PostgreSQL

## Общие вопросы

### Что такое последовательность (sequence) в PostgreSQL?

Последовательность - это объект базы данных, который генерирует уникальные числовые значения. В PostgreSQL последовательности используются для автоматической генерации значений в полях типа `SERIAL` или `BIGSERIAL`.

### Почему возникают ошибки с последовательностями?

Ошибки возникают из-за:
1. **Неправильного именования** - после переименования таблицы последовательность может остаться со старым именем
2. **Отсутствия прав доступа** - пользователь приложения не имеет прав на использование последовательности
3. **Неправильной миграции** - миграция не переименовывает последовательность или не выдает права доступа

## Типичные ошибки

### Ошибка: `InsufficientPrivilegeError: недостаточно прав для доступа к последовательности`

**Причина:** Пользователь приложения не имеет прав на использование последовательности.

**Решение:**
```sql
GRANT ALL PRIVILEGES ON SEQUENCE sequence_name TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE sequence_name TO PUBLIC;
ALTER SEQUENCE sequence_name OWNER TO postgres;
```

**Автоматическое исправление:**
- Используйте `BaseRepository` - он автоматически исправляет права доступа
- Запустите `scripts/check-sequences-after-migration.ps1 -TableName <table_name>`

### Ошибка: `PendingRollbackError: This Session's transaction has been rolled back`

**Причина:** Предыдущая ошибка последовательности привела к откату транзакции.

**Решение:**
1. Исправить права доступа на последовательность (см. выше)
2. Использовать `BaseRepository` для автоматической обработки ошибок
3. Убедиться, что миграция правильно настроена

### Ошибка: Последовательность не найдена или имеет неправильное имя

**Причина:** После переименования таблицы последовательность осталась со старым именем.

**Решение:**
```sql
-- Переименовать последовательность
ALTER SEQUENCE old_name_id_seq RENAME TO new_name_id_seq;

-- Выдать права доступа
GRANT ALL PRIVILEGES ON SEQUENCE new_name_id_seq TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE new_name_id_seq TO PUBLIC;
ALTER SEQUENCE new_name_id_seq OWNER TO postgres;
```

**Автоматическое исправление:**
- Запустите `scripts/check-sequences-after-migration.ps1 -TableName <table_name>`
- Скрипт автоматически переименует последовательность и выдаст права доступа

## Работа с миграциями

### Как правильно создать миграцию с переименованием таблицы?

1. Используйте шаблон `backend/migrations/TEMPLATE_with_sequence.sql`
2. Обязательно переименуйте последовательность:
   ```sql
   ALTER SEQUENCE old_table_name_id_seq RENAME TO new_table_name_id_seq;
   ```
3. Обязательно выдайте права доступа:
   ```sql
   GRANT ALL PRIVILEGES ON SEQUENCE new_table_name_id_seq TO postgres;
   GRANT ALL PRIVILEGES ON SEQUENCE new_table_name_id_seq TO PUBLIC;
   ALTER SEQUENCE new_table_name_id_seq OWNER TO postgres;
   ```

### Как проверить миграцию перед применением?

```powershell
.\scripts\validate-migration.ps1 -MigrationFile "backend\migrations\XXX_migration.sql"
```

### Как проверить последовательности после миграции?

```powershell
.\scripts\check-sequences-after-migration.ps1 -TableName "table_name"
```

## Работа с репозиториями

### Как использовать BaseRepository?

```python
from app.adapters.db.base_repository import BaseRepository

class MyRepository(BaseRepository):
    async def create(self, data: dict):
        try:
            entry = MyModel(**data)
            self.session.add(entry)
            await self.session.flush()
            return entry
        except Exception as e:
            # Автоматическая обработка ошибок последовательностей
            if await self._handle_sequence_error(e, "my_table"):
                # Повторить после исправления
                entry = MyModel(**data)
                self.session.add(entry)
                await self.session.flush()
                return entry
            raise
```

### Какие репозитории должны использовать BaseRepository?

Все репозитории, работающие с таблицами, использующими `SERIAL` или `BIGSERIAL` поля:
- `DomainQueueRepository` ✅ (уже использует)
- Другие репозитории с SERIAL полями

## Мониторинг и отладка

### Как проверить, есть ли ошибки последовательностей в логах?

```powershell
# Разовая проверка
.\scripts\monitor-sequence-errors.ps1

# Непрерывный мониторинг
.\scripts\monitor-sequence-errors.ps1 -Watch -WatchInterval 30
```

### Как проверить существование последовательности вручную?

```sql
-- Проверить все последовательности для таблицы
SELECT sequence_name 
FROM information_schema.sequences 
WHERE sequence_name LIKE '%table_name%';
```

### Как проверить права доступа на последовательность?

```sql
-- Проверить права доступа
\dp sequence_name

-- Или через SQL
SELECT 
    sequence_name,
    sequence_schema,
    data_type
FROM information_schema.sequences
WHERE sequence_name = 'sequence_name';
```

## Тестирование

### Как запустить тесты последовательностей?

```bash
# Из директории backend
pytest tests/test_migrations.py -v

# Пропустить тесты PostgreSQL (если БД недоступна)
SKIP_POSTGRES_TESTS=true pytest tests/test_migrations.py -v
```

### Какие тесты проверяют последовательности?

- `test_domains_queue_sequence_exists` - проверка существования последовательности
- `test_domains_queue_sequence_permissions` - проверка прав доступа
- `test_domains_queue_sequence_name_consistency` - проверка правильности имени
- `test_all_sequences_have_permissions` - проверка всех последовательностей
- `test_sequence_owner_is_postgres` - проверка владельца
- `test_no_orphaned_sequences` - проверка отсутствия "осиротевших" последовательностей

## Автоматизация

### Pre-commit hook

Pre-commit hook автоматически проверяет миграции перед коммитом:
- Проверяет наличие переименования последовательностей
- Проверяет наличие прав доступа на последовательности

Если проверка не прошла - коммит будет отклонен.

### BaseRepository

`BaseRepository` автоматически:
- Обнаруживает ошибки последовательностей
- Исправляет права доступа
- Переименовывает последовательности при необходимости
- Логирует все исправления

## Связанные документы

- `docs/TROUBLESHOOTING.md` - Библия ошибок и решений
- `docs/MIGRATION_CHECKLIST.md` - Чеклист для миграций
- `backend/migrations/TEMPLATE_with_sequence.sql` - Шаблон для миграций
- `backend/app/adapters/db/base_repository.py` - Базовый класс репозитория

## Полезные команды

```powershell
# Проверить миграцию
.\scripts\validate-migration.ps1 -MigrationFile "backend\migrations\XXX_migration.sql"

# Проверить последовательности после миграции
.\scripts\check-sequences-after-migration.ps1 -TableName "table_name"

# Мониторинг ошибок
.\scripts\monitor-sequence-errors.ps1 -Watch

# Запустить тесты
pytest backend/tests/test_migrations.py -v
```

## Примеры правильных миграций

См. `backend/migrations/004_fix_domains_queue_primary_key.sql` - пример правильной миграции с переименованием таблицы и последовательности.













