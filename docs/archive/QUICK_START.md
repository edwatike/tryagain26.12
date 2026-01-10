⚠️ **АРХИВ. Актуальная версия: см. `docs/MASTER_INSTRUCTION.md`**

# Быстрый запуск B2B Platform

## Предварительные требования

1. **Python 3.12+** - установлен и доступен в PATH
2. **Node.js 18+** - установлен и доступен в PATH
3. **PostgreSQL 15** - установлен и запущен
4. **Google Chrome** - установлен

## Шаг 1: Настройка базы данных

```powershell
# Создать базу данных
createdb -U postgres b2b_dev

# Или через psql:
psql -U postgres
CREATE DATABASE b2b_dev;
\q

# Применить миграции
psql -U postgres -d b2b_dev -f backend/migrations/001_initial_schema.sql
```

## Шаг 2: Настройка переменных окружения

### Backend
```powershell
cd backend
copy .env.example .env
# Отредактируйте .env файл при необходимости
```

### Frontend
```powershell
cd frontend\moderator-dashboard-ui
copy .env.local.example .env.local
# Отредактируйте .env.local:
# NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
# NEXT_PUBLIC_CHECKO_API_KEY=your_api_key_here
```

### Parser Service
```powershell
cd parser_service
copy .env.example .env
# Отредактируйте .env при необходимости
```

## Шаг 3: Запуск серверов

Откройте **4 отдельных терминала PowerShell**:

### Терминал 1: Chrome CDP
```powershell
.\start-chrome.bat
```
Или вручную:
```powershell
# Chrome запускается в видимом режиме (не headless), чтобы можно было пройти капчу вручную
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --disable-gpu
```

### Терминал 2: Parser Service
```powershell
.\start-parser.bat
```
Или вручную:
```powershell
cd parser_service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
python run_api.py
```

### Терминал 3: Backend
```powershell
.\start-backend.bat
```
Или вручную:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Терминал 4: Frontend
```powershell
.\start-frontend.bat
```
Или вручную:
```powershell
cd frontend\moderator-dashboard-ui
npm install
npm run dev
```

## Шаг 4: Проверка работоспособности

Откройте в браузере:

1. **Frontend**: http://localhost:3000
2. **Backend API**: http://127.0.0.1:8000/health
3. **Backend Docs**: http://127.0.0.1:8000/docs
4. **Parser Service**: http://127.0.0.1:9003/health
5. **Chrome CDP**: http://127.0.0.1:9222/json/version

## Порядок запуска (важно!)

1. **Сначала** запустите Chrome CDP
2. **Затем** Parser Service
3. **Затем** Backend
4. **В последнюю очередь** Frontend

## Устранение проблем

### Ошибка: "Port already in use"
Закройте процесс, использующий порт:
```powershell
# Найти процесс на порту 8000
netstat -ano | findstr :8000
# Убить процесс (замените PID)
taskkill /PID <PID> /F
```

### Ошибка: "Database connection error"
Проверьте:
- PostgreSQL запущен
- База данных `b2b_dev` создана
- Правильные credentials в `.env`

### Ошибка: "Chrome CDP not available"
Убедитесь, что Chrome запущен с флагом `--remote-debugging-port=9222`

### Ошибка: "Module not found"
Установите зависимости:
```powershell
# Backend
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend
cd frontend\moderator-dashboard-ui
npm install

# Parser
cd parser_service
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Альтернативный способ (один скрипт)

Создайте файл `start-all.ps1`:

```powershell
# start-all.ps1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-chrome.bat"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-parser.bat"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-backend.bat"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\start-frontend.bat"
```

Запустите:
```powershell
.\start-all.ps1
```

