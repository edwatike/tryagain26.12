# B2B Platform

Система для автоматизации поиска, парсинга и модерации поставщиков с интеграцией Checko API.

## 📚 Документация

**⚠️ ВАЖНО: Перед началом работы изучи документацию!**

- **Главная инструкция**: [`docs/MASTER_INSTRUCTION.md`](docs/MASTER_INSTRUCTION.md) - **НАЧНИ ОТСЮДА!**
- **Библия ошибок**: [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) - все ошибки и решения
- **Критические точки**: [`docs/CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md`](docs/CRITICAL_INTEGRATIONS_AND_CHECKLISTS.md) - критические точки интеграции и чеклисты
- **Спецификация API**: [`docs/PROJECT_SPECIFICATION.md`](docs/PROJECT_SPECIFICATION.md) - детальная спецификация API
- **Карта проекта**: [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md) - структура проекта

**При возникновении ошибки:**
1. СНАЧАЛА проверь [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
2. Если решения нет - реши и ОБЯЗАТЕЛЬНО задокументируй

---

## Технологический стек

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python), SQLAlchemy 2.0, PostgreSQL
- **Parser Service**: FastAPI, Playwright, Chrome CDP
- **База данных**: PostgreSQL 15 (база `b2bplatform`)

## Быстрый старт

**Один клик - все сервисы запущены:**

```batch
start-all-tabby.bat
```

**Откройте:** http://localhost:3000

**📖 Подробная документация:** [`docs/MASTER_INSTRUCTION.md`](docs/MASTER_INSTRUCTION.md) - раздел "3. Быстрый старт"

## Структура проекта

```
tryagain/
├── backend/              # Backend сервис (FastAPI)
├── frontend/
│   └── moderator-dashboard-ui/  # Next.js Frontend
├── parser_service/       # Parser Service
├── docs/                 # Документация
├── scripts/              # Скрипты автоматизации
└── logs/                 # Логи сервисов
```

**📖 Подробная структура:** [`docs/PROJECT_MAP.md`](docs/PROJECT_MAP.md)

## Порты и сервисы

- **Backend:** `8000` (http://127.0.0.1:8000)
- **Frontend:** `3000` (http://localhost:3000)
- **Parser Service:** `9003` (http://127.0.0.1:9003)
- **Chrome CDP:** `9222` (http://127.0.0.1:9222)

## Разработка

### Backend тесты

```powershell
cd backend
pytest
```

### Frontend линтинг

```powershell
cd frontend/moderator-dashboard-ui
npm run lint
npm run type-check
```

### Проверка импортов (Backend)

```powershell
python temp/backend/check_imports.py
```

**📖 Подробная документация:** [`docs/MASTER_INSTRUCTION.md`](docs/MASTER_INSTRUCTION.md)

---

**Лицензия:** MIT
