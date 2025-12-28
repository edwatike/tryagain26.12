# Скрипт для исправления зависших parsing runs
# Находит parsing runs со статусом "running", у которых есть домены в domains_queue
# и обновляет их статус на "completed"

param(
    [string]$ProjectRoot = $PSScriptRoot
)

Write-Host "=== Исправление зависших parsing runs ===" -ForegroundColor Cyan
Write-Host ""

$env:PGPASSWORD = "Jnvnszoe5971312059001"

# Найти parsing runs со статусом "running", которые стартовали более 5 минут назад
# Это означает, что парсинг, скорее всего, завершился, но статус не обновился
$query = @"
SELECT pr.run_id, COUNT(dq.id) as domains_count, pr.started_at, NOW() - pr.started_at as elapsed_time
FROM parsing_runs pr
LEFT JOIN domains_queue dq ON dq.parsing_run_id = pr.run_id
WHERE pr.status = 'running' 
  AND pr.started_at < NOW() - INTERVAL '5 minutes'
GROUP BY pr.run_id, pr.started_at
ORDER BY pr.started_at DESC;
"@

Write-Host "Поиск зависших parsing runs с доменами..." -ForegroundColor Yellow
$result = psql -U postgres -d b2bplatform -h localhost -p 5432 -c $query -t -A -F "|"

if (-not $result -or $result -eq "") {
    Write-Host "✅ Нет зависших parsing runs с доменами" -ForegroundColor Green
    exit 0
}

$runsToFix = @()
$result | ForEach-Object {
    if ($_ -match '\|') {
        $fields = $_ -split '\|'
        $runsToFix += @{
            run_id = $fields[0].Trim()
            domains_count = [int]$fields[1].Trim()
        }
    }
}

Write-Host "Найдено parsing runs для исправления: $($runsToFix.Count)" -ForegroundColor Yellow
Write-Host ""

foreach ($run in $runsToFix) {
    $domainsCount = if ($run.domains_count) { $run.domains_count } else { 0 }
    Write-Host "Исправление run_id: $($run.run_id) (доменов: $domainsCount)" -ForegroundColor Cyan
    
    # Обновить статус на "completed" и установить results_count
    # Если доменов нет, все равно помечаем как completed (парсинг завершился, но результатов нет)
    $updateQuery = @"
UPDATE parsing_runs 
SET status = 'completed',
    finished_at = COALESCE(finished_at, NOW()),
    results_count = $domainsCount
WHERE run_id = '$($run.run_id)' AND status = 'running';
"@
    
    $updateResult = psql -U postgres -d b2bplatform -h localhost -p 5432 -c $updateQuery -t -A
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Обновлен: $($run.run_id) (статус: completed, доменов: $domainsCount)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Ошибка при обновлении: $($run.run_id)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Исправление завершено ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Проверка результатов..." -ForegroundColor Yellow

# Проверить результаты
$checkQuery = @"
SELECT run_id, status, results_count, finished_at
FROM parsing_runs
WHERE run_id IN ($(($runsToFix | ForEach-Object { "'$($_.run_id)'" }) -join ','));
"@

$checkResult = psql -U postgres -d b2bplatform -h localhost -p 5432 -c $checkQuery -t -A -F "|"
Write-Host ""
Write-Host "Обновленные parsing runs:" -ForegroundColor Yellow
$checkResult | ForEach-Object {
    if ($_ -match '\|') {
        $fields = $_ -split '\|'
        Write-Host "  run_id: $($fields[0])"
        Write-Host "    status: $($fields[1])"
        Write-Host "    results_count: $($fields[2])"
        Write-Host "    finished_at: $($fields[3])"
        Write-Host ""
    }
}

