⚠️ **АРХИВ. Актуальная версия: см. `docs/MASTER_INSTRUCTION.md`**

# Создание .env файла

## Backend

Создайте файл `backend/.env` со следующим содержимым:

```env
DATABASE_URL=postgresql+asyncpg://postgres:Jnvnszoe5971312059001@localhost:5432/b2bplatform
PARSER_SERVICE_URL=http://127.0.0.1:9003
ENV=development
LOG_LEVEL=INFO
LOG_SQL=false
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ATTACHMENTS_DIR=storage/attachments
```

**⚠️ ВАЖНО:** 
- Используется база данных `b2bplatform` (НЕ МЕНЯТЬ!)
- Пароль: `Jnvnszoe5971312059001`
- Подробности: см. `docs/DATABASE_CONFIG.md`

## Frontend

Создайте файл `frontend/moderator-dashboard-ui/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_CHECKO_API_KEY=your_checko_api_key_here
```

## Parser Service

Создайте файл `parser_service/.env`:

```env
CHROME_CDP_URL=http://127.0.0.1:9222
LOG_LEVEL=INFO
```

## Быстрое создание (PowerShell)

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

