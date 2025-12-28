# Скрипт принудительного перезапуска Backend с полной очисткой кэша
# Использование: .\scripts\force-restart-backend.ps1

param(
    [string]$ProjectRoot = $PSScriptRoot
)

Write-Host "=== Принудительный перезапуск Backend с полной очисткой кэша ===" -ForegroundColor Cyan
Write-Host ""

# ШАГ 1: Остановить все процессы Python
Write-Host "ШАГ 1: Остановка всех процессов Python..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*tryagain*" }
if ($pythonProcesses) {
    Write-Host "Найдено процессов Python: $($pythonProcesses.Count)"
    $pythonProcesses | ForEach-Object {
        Write-Host "  Остановка процесса: $($_.Id) - $($_.ProcessName)"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    
    # Проверить, что все остановлены
    $remaining = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*tryagain*" }
    if ($remaining) {
        Write-Host "⚠️  Предупреждение: Некоторые процессы Python все еще запущены!" -ForegroundColor Red
        $remaining | ForEach-Object {
            Write-Host "  Процесс: $($_.Id) - $($_.ProcessName)"
        }
    } else {
        Write-Host "✅ Все процессы Python остановлены" -ForegroundColor Green
    }
} else {
    Write-Host "✅ Процессы Python не найдены" -ForegroundColor Green
}

# ШАГ 2: Очистить кэш Python
Write-Host ""
Write-Host "ШАГ 2: Очистка кэша Python..." -ForegroundColor Yellow
$cacheDirs = Get-ChildItem -Path "$ProjectRoot\backend" -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue
if ($cacheDirs) {
    Write-Host "Найдено директорий __pycache__: $($cacheDirs.Count)"
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Директории __pycache__ удалены" -ForegroundColor Green
} else {
    Write-Host "✅ Директории __pycache__ не найдены" -ForegroundColor Green
}

$pycFiles = Get-ChildItem -Path "$ProjectRoot\backend" -Recurse -Filter "*.pyc" -File -ErrorAction SilentlyContinue
if ($pycFiles) {
    Write-Host "Найдено .pyc файлов: $($pycFiles.Count)"
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "✅ .pyc файлы удалены" -ForegroundColor Green
} else {
    Write-Host "✅ .pyc файлы не найдены" -ForegroundColor Green
}

# Проверить, что кэш очищен
$remainingCache = Get-ChildItem -Path "$ProjectRoot\backend" -Recurse -Filter "__pycache__" -Directory -ErrorAction SilentlyContinue
if ($remainingCache) {
    Write-Host "⚠️  Предупреждение: Некоторые директории __pycache__ все еще существуют!" -ForegroundColor Red
} else {
    Write-Host "✅ Кэш полностью очищен" -ForegroundColor Green
}

# ШАГ 3: Запустить Backend
Write-Host ""
Write-Host "ШАГ 3: Запуск Backend..." -ForegroundColor Yellow
$backendPath = Join-Path $ProjectRoot "backend"
if (-not (Test-Path $backendPath)) {
    Write-Host "❌ Ошибка: Директория backend не найдена: $backendPath" -ForegroundColor Red
    exit 1
}

$venvPath = Join-Path $backendPath "venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Ошибка: Виртуальное окружение не найдено: $venvPath" -ForegroundColor Red
    exit 1
}

Write-Host "Запуск Backend в новом окне PowerShell..."
$script = @"
cd `"$backendPath`"
& `"$venvPath`"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $script -WindowStyle Normal
Write-Host "✅ Backend запущен в новом окне PowerShell" -ForegroundColor Green

# ШАГ 4: Ожидание запуска и проверка
Write-Host ""
Write-Host "ШАГ 4: Ожидание запуска Backend..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

$maxAttempts = 30
$attempt = 0
$backendStarted = $false

do {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($health.status -eq "ok") {
            Write-Host "✅ Backend запущен и отвечает на запросы!" -ForegroundColor Green
            $backendStarted = $true
            break
        }
    } catch {
        # Продолжить ожидание
    }
    Write-Host "  Попытка $attempt/$maxAttempts..." -ForegroundColor Gray
} while ($attempt -lt $maxAttempts)

if (-not $backendStarted) {
    Write-Host "⚠️  Предупреждение: Backend не ответил в течение 60 секунд" -ForegroundColor Yellow
    Write-Host "Проверьте окно PowerShell с Backend вручную" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Перезапуск завершен ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host "1. Проверьте окно PowerShell с Backend на наличие ошибок"
Write-Host "2. Проверьте endpoint: http://127.0.0.1:8000/health"
Write-Host "3. Протестируйте endpoint: http://127.0.0.1:8000/parsing/runs/{run_id}"
Write-Host ""
Write-Host "Если ошибка AttributeError все еще возникает, перезагрузите компьютер" -ForegroundColor Red



