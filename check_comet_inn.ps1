$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/runs/c3e59c47-010e-4325-b131-3a8e86853d06" -Method Get
$processLog = $response.process_log
$lastComet = $processLog.comet.runs | Get-Member -MemberType NoteProperty | Select-Object -Last 1 -ExpandProperty Name
$lastRun = $processLog.comet.runs.$lastComet

Write-Host "Последний Comet запуск: $lastComet"
Write-Host "Результаты:"
$lastRun.results | ConvertTo-Json -Depth 10
