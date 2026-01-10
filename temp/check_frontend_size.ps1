# Скрипт для проверки размеров фронтенда
$frontendPath = "d:\tryagain\frontend\moderator-dashboard-ui"

Write-Host "Проверка размеров фронтенда..." -ForegroundColor Cyan
Write-Host ""

# Общий размер
$total = (Get-ChildItem -Path $frontendPath -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
Write-Host "Общий размер: $([math]::Round($total/1GB, 2)) GB" -ForegroundColor Yellow

# node_modules
if (Test-Path "$frontendPath\node_modules") {
    $nodeSize = (Get-ChildItem -Path "$frontendPath\node_modules" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $nodePercent = [math]::Round($nodeSize/$total*100, 1)
    Write-Host "node_modules: $([math]::Round($nodeSize/1GB, 2)) GB ($nodePercent%)" -ForegroundColor $(if ($nodePercent -gt 80) { "Red" } else { "Yellow" })
} else {
    Write-Host "node_modules: не найден" -ForegroundColor Green
}

# .next
if (Test-Path "$frontendPath\.next") {
    $nextSize = (Get-ChildItem -Path "$frontendPath\.next" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $nextPercent = [math]::Round($nextSize/$total*100, 1)
    Write-Host ".next: $([math]::Round($nextSize/1GB, 2)) GB ($nextPercent%)" -ForegroundColor Yellow
} else {
    Write-Host ".next: не найден" -ForegroundColor Green
}

# Другие файлы
$otherSize = $total - $nodeSize - $nextSize
Write-Host "Другие файлы: $([math]::Round($otherSize/1MB, 2)) MB" -ForegroundColor Green

Write-Host ""
Write-Host "Рекомендации:" -ForegroundColor Cyan
if ($total -gt 1GB) {
    Write-Host "⚠️  Размер фронтенда превышает 1 GB!" -ForegroundColor Red
    Write-Host "   Это нормально для Next.js проекта с node_modules" -ForegroundColor Yellow
    Write-Host "   node_modules обычно занимает 80-95% от общего размера" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Что можно сделать:" -ForegroundColor Cyan
    Write-Host "   1. Добавить node_modules в .gitignore (если еще не добавлен)" -ForegroundColor White
    Write-Host "   2. Использовать .npmrc для оптимизации установки" -ForegroundColor White
    Write-Host "   3. Проверить дублирующиеся зависимости" -ForegroundColor White
    Write-Host "   4. Использовать npm ci вместо npm install в CI/CD" -ForegroundColor White
} else {
    Write-Host "✅ Размер в пределах нормы" -ForegroundColor Green
}

