# Script to monitor all services and display logs with colors
# Usage: .\scripts\monitor-services.ps1 -ProjectRoot "D:\tryagain"

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot
)

# Load logger functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptPath\logger.ps1"

# Clear screen
Clear-Host

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Main Monitor - All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info -Service "Monitor" -Message "Monitoring all services..."
Write-Info -Service "Monitor" -Message "Press Ctrl+C to stop monitoring"
Write-Host ""

# Function to check service health
function Check-ServiceHealth {
    param([string]$ServiceName, [string]$Url, [int]$Port)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success -Service $ServiceName -Message "Service is running on $Url (HTTP $($response.StatusCode))"
            return $true
        } else {
            Write-Warning -Service $ServiceName -Message "Service returned HTTP $($response.StatusCode) on $Url"
            return $false
        }
    } catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -like "*connection*" -or $errorMsg -like "*refused*") {
            Write-Error -Service $ServiceName -Message "Service not responding on $Url - Connection refused"
        } elseif ($errorMsg -like "*timeout*") {
            Write-Error -Service $ServiceName -Message "Service timeout on $Url - Service may be starting"
        } else {
            Write-Error -Service $ServiceName -Message "Service error on $Url - $errorMsg"
        }
        return $false
    }
}

# Function to check port
function Check-Port {
    param([int]$Port, [string]$ServiceName)
    
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Success -Service $ServiceName -Message "Port $Port is listening"
        return $true
    } else {
        Write-Error -Service $ServiceName -Message "Port $Port is not listening"
        return $false
    }
}

# Initial health check
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Initial Health Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Chrome CDP
Check-Port -Port 9222 -ServiceName "Chrome CDP"
Start-Sleep -Seconds 1

# Check Parser Service
Check-ServiceHealth -ServiceName "Parser Service" -Url "http://127.0.0.1:9003/health" -Port 9003
Start-Sleep -Seconds 1

# Check Backend
Check-ServiceHealth -ServiceName "Backend" -Url "http://127.0.0.1:8000/health" -Port 8000
Start-Sleep -Seconds 1

# Check Frontend
Check-ServiceHealth -ServiceName "Frontend" -Url "http://localhost:3000" -Port 3000
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Continuous Monitoring" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info -Service "Monitor" -Message "Monitoring services every 10 seconds..."
Write-Host ""

# Continuous monitoring loop
$iteration = 0
while ($true) {
    $iteration++
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] Health Check #$iteration" -ForegroundColor Gray
    Write-Host ""
    
    # Check all services
    $chromeOk = Check-Port -Port 9222 -ServiceName "Chrome CDP"
    $parserOk = Check-ServiceHealth -ServiceName "Parser Service" -Url "http://127.0.0.1:9003/health" -Port 9003
    $backendOk = Check-ServiceHealth -ServiceName "Backend" -Url "http://127.0.0.1:8000/health" -Port 8000
    $frontendOk = Check-ServiceHealth -ServiceName "Frontend" -Url "http://localhost:3000" -Port 3000
    
    Write-Host ""
    
    # Summary
    if ($chromeOk -and $parserOk -and $backendOk -and $frontendOk) {
        Write-Success -Service "Monitor" -Message "All services are running correctly"
    } else {
        Write-Warning -Service "Monitor" -Message "Some services are not responding"
    }
    
    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Gray
    Write-Host ""
    
    Start-Sleep -Seconds 10
}

