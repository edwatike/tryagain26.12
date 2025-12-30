# Скрипты для работы с базой данных

## Резервное копирование

### Linux/macOS
```bash
chmod +x backup_database.sh
./backup_database.sh [database_name] [backup_dir]
```

### Windows
```cmd
backup_database.bat [database_name] [backup_dir]
```

**Параметры:**
- `database_name` - имя базы данных (по умолчанию: `b2b`)
- `backup_dir` - директория для сохранения бэкапов (по умолчанию: `./backups`)

**Переменные окружения:**
- `DB_USER` - пользователь PostgreSQL (по умолчанию: `postgres`)
- `DB_HOST` - хост PostgreSQL (по умолчанию: `localhost`)
- `DB_PORT` - порт PostgreSQL (по умолчанию: `5432`)

**Пример:**
```bash
export DB_USER=postgres
export DB_HOST=localhost
./backup_database.sh b2b ./backups
```

**Восстановление из бэкапа:**
```bash
# Для SQL файла
psql -U postgres -d b2b < backup_b2b_20251226_120000.sql

# Для сжатого файла
gunzip backup_b2b_20251226_120000.sql.gz
psql -U postgres -d b2b < backup_b2b_20251226_120000.sql
```

## Проверка целостности данных

```bash
cd backend
python ../scripts/check_data_integrity.py
```

Скрипт проверяет:
- Количество записей в каждой таблице
- Наличие некорректных данных (пустые имена, невалидные домены)
- Целостность foreign keys
- Наличие orphaned записей

**Выходной код:**
- `0` - целостность данных в порядке
- `1` - найдены проблемы с целостностью

## Автоматизация резервного копирования

### Linux (cron)
Добавьте в crontab для ежедневного бэкапа в 2:00 ночи:
```bash
0 2 * * * /path/to/scripts/backup_database.sh b2b /path/to/backups
```

### Windows (Task Scheduler)
1. Откройте Task Scheduler
2. Создайте новую задачу
3. Установите триггер на ежедневное выполнение в 2:00
4. Установите действие: запуск `backup_database.bat`

## Инструменты для проверки качества кода

### Быстрая проверка сервисов

**`quick-check.ps1`** - Проверка работоспособности сервисов

```powershell
# Проверить все сервисы
.\scripts\quick-check.ps1 all

# Проверить только Backend
.\scripts\quick-check.ps1 backend

# Проверить только Frontend
.\scripts\quick-check.ps1 frontend

# Проверить только Parser Service
.\scripts\quick-check.ps1 parser
```

**Что проверяется:**
- Backend: импорты, health endpoint
- Frontend: линтер, доступность
- Parser Service: health endpoint, Chrome CDP

### Pre-commit hook

**`pre-commit.ps1`** - Автоматические проверки перед коммитом

**Установка:**
```powershell
.\scripts\setup-pre-commit.ps1
```

**Что проверяется:**
- Импорты Backend (`temp/backend/check_imports.py`)
- Линтер Frontend (`npm run lint`)

**Использование:**
Hook запускается автоматически при каждом `git commit`. Если проверки не пройдены, коммит будет отклонен.

**Отключение (временно):**
```bash
git commit --no-verify
```

## Шаблоны для разработки

### Тестирование гипотез

**`temp/templates/test_hypothesis_template.py`** - Шаблон для тестирования гипотез

**Использование:**
1. Скопируйте шаблон: `copy temp\templates\test_hypothesis_template.py temp\test_my_hypothesis.py`
2. Заполните TODO комментарии
3. Запустите: `python temp\test_my_hypothesis.py`

**Пример:**
```python
# temp/test_blacklist_hypothesis.py
def test_hypothesis():
    # Проверка добавления домена в blacklist
    response = requests.post(f"{BASE_URL}/moderator/blacklist", json={"domain": "test.ru"})
    assert response.status_code == 201
    # ... остальная логика
```

### Документирование ошибок

**`temp/templates/troubleshooting_template.md`** - Шаблон для документирования ошибок

**Использование:**
1. Откройте шаблон
2. Заполните все поля
3. Скопируйте в `docs/TROUBLESHOOTING.md`

**Важно:** Каждая ошибка ДОЛЖНА быть задокументирована в `docs/TROUBLESHOOTING.md`









