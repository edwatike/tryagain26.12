# Скрипт для принудительного перезапуска Backend с очисткой кэша
# Использование: .\scripts\restart-backend-with-cache-clear.ps1

param(
    [string]$ProjectRoot = $PSScriptRoot
)

Write-Host "========================================"
Write-Host "Перезапуск Backend с очисткой кэша"
Write-Host "========================================"

# 1. Остановка всех процессов Backend
Write-Host "`n[1/5] Остановка процессов Backend..."
$pids = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($pids) {
    Write-Host "  Найдено процессов: $($pids.Count)"
    $pids | ForEach-Object { 
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        Write-Host "  Остановлен процесс: $_"
    }
    Start-Sleep -Seconds 3
} else {
    Write-Host "  Процессы не найдены"
}

# Проверка, что все остановлено
$remaining = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($remaining) {
    Write-Host "  ⚠️  Предупреждение: некоторые процессы все еще запущены"
} else {
    Write-Host "  ✅ Все процессы остановлены"
}

# 2. Очистка Python кэша
Write-Host "`n[2/5] Очистка Python кэша..."
$cacheDirs = Get-ChildItem -Path "$ProjectRoot\backend" -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue
$pycFiles = Get-ChildItem -Path "$ProjectRoot\backend" -Recurse -Filter "*.pyc" -File -ErrorAction SilentlyContinue

if ($cacheDirs) {
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Удалено директорий __pycache__: $($cacheDirs.Count)"
}
if ($pycFiles) {
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "  Удалено .pyc файлов: $($pycFiles.Count)"
}
Write-Host "  ✅ Кэш очищен"

# 3. Проверка кода
Write-Host "`n[3/5] Проверка кода..."
$getParsingRunFile = "$ProjectRoot\backend\app\usecases\get_parsing_run.py"
if (Test-Path $getParsingRunFile) {
    $hasSafeAccess = Get-Content $getParsingRunFile | Select-String -Pattern "__dict__" -Quiet
    if ($hasSafeAccess) {
        Write-Host "  ✅ Код содержит безопасный доступ через __dict__"
    } else {
        Write-Host "  ⚠️  Предупреждение: код может не содержать безопасный доступ"
    }
} else {
    Write-Host "  ⚠️  Файл не найден: $getParsingRunFile"
}

# 4. Запуск Backend
Write-Host "`n[4/5] Запуск Backend..."
$backendDir = "$ProjectRoot\backend"
if (Test-Path "$backendDir\venv\Scripts\Activate.ps1") {
    $script = @"
cd '$backendDir'
& .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $script -WindowStyle Minimized
    Write-Host "  Backend запускается..."
} else {
    Write-Host "  ❌ Ошибка: виртуальное окружение не найдено"
    exit 1
}

# 5. Проверка запуска
Write-Host "`n[5/5] Проверка запуска Backend..."
$maxAttempts = 30
$attempt = 0
$success = $false

do {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($response.status -eq "ok") {
            Write-Host "  ✅ Backend успешно запущен!"
            $success = $true
            break
        }
    } catch {
        # Продолжаем попытки
    }
    Write-Host "  Попытка $attempt/$maxAttempts..."
} while ($attempt -lt $maxAttempts)

if (-not $success) {
    Write-Host "  ❌ Ошибка: Backend не запустился за $maxAttempts попыток"
    Write-Host "  Проверьте логи в директории logs/"
    exit 1
}

Write-Host "`n========================================"
Write-Host "Перезапуск завершен успешно!"
Write-Host "========================================"
Write-Host "Backend доступен на: http://127.0.0.1:8000"
Write-Host "Документация API: http://127.0.0.1:8000/docs"
Write-Host ""










