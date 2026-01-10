$ErrorActionPreference='Stop'

# Get latest runId
$runs = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/parsing/runs?limit=1'
$runId = $runs.runs[0].runId
Write-Host "Using runId: $runId"

# Start Comet batch
$payload = @{
    runId = $runId
    domains = @('site1.com','site2.org','site3.net')
} | ConvertTo-Json -Compress
Write-Host "Payload: $payload"

$start = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/comet/extract-batch' -ContentType 'application/json' -Body $payload
$cometRunId = $start.cometRunId
Write-Host "Started cometRunId: $cometRunId"

# Poll status
for($i=1; $i -le 60; $i++){
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/comet/status/$runId?cometRunId=$cometRunId"
    Write-Host "[$i/60] status=$($status.status) processed=$($status.processed)/$($status.total)"
    if($status.status -in @('completed','failed')){ break }
    Start-Sleep -Seconds 2
}

# Verify persistence
$run = Invoke-RestMethod -Uri "http://127.0.0.1:8000/parsing/runs/$runId"
$pl = $run.processLog
if(-not $pl){ $pl = $run.process_log }
if(-not $pl){ throw 'process_log missing' }

$runState = $pl.comet.runs.$cometRunId
if(-not $runState){ throw 'Comet run not found in process_log' }

Write-Host "=== Persisted Comet run ==="
$runState | ConvertTo-Json -Depth 8
