# 🚀 Запуск B2B Platform - Инструкция

## Шаг 1: Создайте .env файлы

Выполните в PowerShell (из корня проекта):

```powershell
# Backend
@" 
DATABASE_URL=postgresql+asyncpg://postgres:Jnvnszoe5971312059001@localhost:5432/b2bplatform
PARSER_SERVICE_URL=http://127.0.0.1:9003
ENV=development
LOG_LEVEL=INFO
LOG_SQL=false
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ATTACHMENTS_DIR=storage/attachments
"@ | Out-File -FilePath "backend\.env" -Encoding utf8

# Frontend
@"
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_CHECKO_API_KEY=your_checko_api_key_here
"@ | Out-File -FilePath "frontend\moderator-dashboard-ui\.env.local" -Encoding utf8

# Parser
@"
CHROME_CDP_URL=http://127.0.0.1:9222
LOG_LEVEL=INFO
"@ | Out-File -FilePath "parser_service\.env" -Encoding utf8
```

**⚠️ ВАЖНО:** 
- Используется база данных `b2bplatform` (НЕ МЕНЯТЬ!)
- Пароль: `Jnvnszoe5971312059001`
- Подробности: см. `docs/DATABASE_CONFIG.md`

## Шаг 2: Примените миграции БД

```powershell
.\setup-database.bat
```

Или вручную:
```powershell
$env:PGPASSWORD="Jnvnszoe5971312059001"
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\001_initial_schema.sql
psql -U postgres -d b2bplatform -h localhost -p 5432 -f backend\migrations\002_audit_log.sql
```

## Шаг 3: Запустите все сервисы

```powershell
.\start-all.bat
```

## Проверка

Откройте в браузере:
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000/health
- Backend Docs: http://127.0.0.1:8000/docs

## Остановка

```powershell
.\stop-all.bat
```

## Статус

✅ Зависимости установлены
✅ Код исправлен
⚠️ Нужно создать .env файлы
⚠️ Нужно применить миграции БД

