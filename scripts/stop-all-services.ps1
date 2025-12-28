# Script to stop all services
# Usage: .\scripts\stop-all-services.ps1

Write-Host "Stopping all services..." -ForegroundColor Yellow

# Check if Chrome CDP is accessible before stopping Chrome
$chromeCdpUrl = "http://127.0.0.1:9222/json/version"
try {
    $response = Invoke-WebRequest -Uri $chromeCdpUrl -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "Chrome CDP is accessible - NOT stopping Chrome" -ForegroundColor Green
        Write-Host "Chrome will continue running in CDP mode" -ForegroundColor Green
    }
} catch {
    # Chrome CDP is not accessible, safe to stop Chrome
    Write-Host "Chrome CDP is not accessible - stopping Chrome processes..." -ForegroundColor Yellow
    Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

# Stop processes on specific ports (except Chrome CDP port 9222 if CDP is accessible)
$ports = @(9003, 8000, 3000)
$skipChromePort = $false

# Check Chrome CDP before stopping port 9222
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $skipChromePort = $true
        Write-Host "Skipping port 9222 (Chrome CDP is running)" -ForegroundColor Green
    }
} catch {
    # Chrome CDP not accessible, can stop port 9222
    $ports += 9222
}

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        if ($conn.State -eq "Listen") {
            Write-Host "Stopping process $($conn.OwningProcess) on port $port..." -ForegroundColor Yellow
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}

# Stop Python processes (Backend, Parser)
Write-Host "Stopping Python processes..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Backend*" -or 
    $_.MainWindowTitle -like "*Parser*" -or
    $_.CommandLine -like "*uvicorn*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Node processes (Frontend)
Write-Host "Stopping Node processes..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Frontend*" -or
    $_.CommandLine -like "*next dev*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "All services stopped" -ForegroundColor Green
Start-Sleep -Seconds 2

