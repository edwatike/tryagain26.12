# Полный тест: запуск сервисов, создание parsing run, проверка результатов
param([string]$ProjectRoot = $PSScriptRoot)

Write-Host "=== ПОЛНЫЙ ТЕСТ: Парсинг и отображение результатов ===" -ForegroundColor Cyan
Write-Host ""

# 1. Запуск сервисов
Write-Host "1. Запуск всех сервисов..." -ForegroundColor Yellow
& "$ProjectRoot\start-all-tabby.bat"
Start-Sleep -Seconds 15

# 2. Проверка здоровья сервисов
Write-Host ""
Write-Host "2. Проверка здоровья сервисов..." -ForegroundColor Yellow
$servicesOk = $true

try {
    $backendHealth = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 5
    Write-Host "   ✅ Backend: OK" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Backend: НЕ ДОСТУПЕН" -ForegroundColor Red
    $servicesOk = $false
}

try {
    $parserHealth = Invoke-RestMethod -Uri "http://127.0.0.1:9003/health" -Method Get -TimeoutSec 5
    Write-Host "   ✅ Parser Service: OK" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Parser Service: НЕ ДОСТУПЕН" -ForegroundColor Red
    $servicesOk = $false
}

try {
    $frontendCheck = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✅ Frontend: OK" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Frontend: НЕ ДОСТУПЕН" -ForegroundColor Red
    $servicesOk = $false
}

if (-not $servicesOk) {
    Write-Host ""
    Write-Host "❌ Не все сервисы доступны. Ожидание 10 секунд..." -ForegroundColor Red
    Start-Sleep -Seconds 10
}

# 3. Создание parsing run
Write-Host ""
Write-Host "3. Создание parsing run..." -ForegroundColor Yellow
try {
    $startResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/start" -Method Post -Body (@{
        keyword = "тест парсинг"
        depth = 1
        source = "google"
    } | ConvertTo-Json) -ContentType "application/json"
    
    $runId = $startResponse.runId
    Write-Host "   ✅ Parsing run создан: $runId" -ForegroundColor Green
    Write-Host "   Статус: $($startResponse.status)"
} catch {
    Write-Host "   ❌ Ошибка создания parsing run: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. Ожидание завершения парсинга
Write-Host ""
Write-Host "4. Ожидание завершения парсинга (максимум 2 минуты)..." -ForegroundColor Yellow
$maxWait = 120
$elapsed = 0
$completed = $false

while ($elapsed -lt $maxWait -and -not $completed) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    
    try {
        $statusResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/status/$runId" -Method Get
        $status = $statusResponse.status
        
        Write-Host "   [$elapsed сек] Статус: $status" -NoNewline
        
        if ($status -eq "completed") {
            Write-Host " ✅" -ForegroundColor Green
            $completed = $true
        } elseif ($status -eq "failed") {
            Write-Host " ❌" -ForegroundColor Red
            Write-Host "   Ошибка: $($statusResponse.error)" -ForegroundColor Red
            exit 1
        } else {
            Write-Host ""
        }
    } catch {
        Write-Host "   Ошибка проверки статуса: $($_.Exception.Message)"
    }
}

if (-not $completed) {
    Write-Host ""
    Write-Host "⚠️  Парсинг не завершился за $maxWait секунд" -ForegroundColor Yellow
}

# 5. Проверка доменов через API
Write-Host ""
Write-Host "5. Проверка доменов через API..." -ForegroundColor Yellow
try {
    $domainsResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/domains/queue?parsingRunId=$runId&limit=100" -Method Get
    $domainsCount = $domainsResponse.entries.Count
    $total = $domainsResponse.total
    
    Write-Host "   ✅ API вернул: $domainsCount доменов (total: $total)" -ForegroundColor Green
    
    if ($domainsCount -gt 0) {
        Write-Host "   Первые 3 домена:"
        for ($i = 0; $i -lt [Math]::Min(3, $domainsCount); $i++) {
            Write-Host "     $($i+1). $($domainsResponse.entries[$i].domain) - $($domainsResponse.entries[$i].url)"
        }
    } else {
        Write-Host "   ⚠️  Доменов нет!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Ошибка получения доменов: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 6. Проверка через фронтенд (симуляция)
Write-Host ""
Write-Host "6. Проверка parsing run через API (как фронтенд)..." -ForegroundColor Yellow
try {
    $runResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/runs/$runId" -Method Get
    Write-Host "   ✅ Parsing run получен:" -ForegroundColor Green
    Write-Host "     runId: $($runResponse.runId)"
    Write-Host "     status: $($runResponse.status)"
    Write-Host "     resultsCount: $($runResponse.resultsCount)"
    Write-Host "     keyword: $($runResponse.keyword)"
    
    if ($runResponse.status -eq "completed" -and $runResponse.resultsCount -gt 0) {
        Write-Host ""
        Write-Host "✅✅✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Откройте в браузере: http://localhost:3000/parsing-runs/$runId" -ForegroundColor Cyan
        Write-Host "Должны отображаться $($runResponse.resultsCount) доменов" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "⚠️  Статус: $($runResponse.status), resultsCount: $($runResponse.resultsCount)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== ТЕСТ ЗАВЕРШЕН ===" -ForegroundColor Cyan









