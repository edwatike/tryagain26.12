# Статус запуска серверов

## ✅ Что работает:

1. **Chrome CDP** - запущен на порту 9222 ✅
2. **Frontend зависимости** - установлены ✅
3. **Backend зависимости** - установлены ✅
4. **Parser зависимости** - установлены ✅

## ⚠️ Что нужно сделать:

### 1. Создать .env файлы

Выполните команду PowerShell:

```powershell
# Backend
@"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres
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

### 2. Применить миграции БД

```powershell
.\setup-database.bat
```

Или вручную:
```powershell
psql -U postgres -d postgres -f backend\migrations\001_initial_schema.sql
```

### 3. Запустить все сервисы

```powershell
.\start-all.bat
```

## Проверка работы:

После запуска проверьте:

- Frontend: http://localhost:3000
- Backend: http://127.0.0.1:8000/health
- Backend Docs: http://127.0.0.1:8000/docs
- Parser: http://127.0.0.1:9003/health

## Если что-то не работает:

1. Проверьте, что PostgreSQL запущен
2. Проверьте, что порты 8000, 3000, 9003, 9222 свободны
3. Проверьте логи в окнах сервисов
4. Убедитесь, что .env файлы созданы правильно

