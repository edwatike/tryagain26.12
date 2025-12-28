# Script to start all services in Tabby terminal with tabs and colored logging
# Usage: .\scripts\start-services-tabby.ps1 -ProjectRoot "D:\tryagain"
# This script uses a single-window approach: all services run in background and logs are shown in ONE window

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot
)

# Normalize path (remove quotes and trailing backslash if present)
$ProjectRoot = $ProjectRoot.Trim('"').TrimEnd('\')

# Load logger functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptPath\logger.ps1"

# Change to project root
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting All Services" -ForegroundColor Cyan
Write-Host "  Single Window Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Use the single-window script instead
Write-Info -Service "Tabby" -Message "Using single-window mode (all services in one window)"
Write-Info -Service "Tabby" -Message "Starting unified service manager..."

# Start the single-window script in current window
$singleWindowScript = Join-Path $scriptPath "start-all-services-single-window.ps1"
& powershell.exe -ExecutionPolicy Bypass -File $singleWindowScript -ProjectRoot $ProjectRoot

# Check if Tabby is available
$tabbyPath = Get-Command "tabby" -ErrorAction SilentlyContinue
if (-not $tabbyPath) {
    Write-Warning -Service "Tabby" -Message "Tabby CLI not found. Will use PowerShell windows (Tabby will group them as tabs if configured)."
    Write-Info -Service "Tabby" -Message "You can install Tabby from: https://tabby.sh/"
    Write-Info -Service "Tabby" -Message "Make sure Tabby is set to 'Open new tabs in the same window' in Settings → Window"
}

# Create log directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Function to start service in new Tabby tab (in the same window)
# Uses Tabby CLI if available, otherwise uses PowerShell with proper window grouping
function Start-ServiceInTab {
    param(
        [string]$TabName,
        [string]$ServiceName,
        [string]$Command,
        [string]$WorkingDir
    )
    
    Write-Info -Service "Tabby" -Message "Starting $ServiceName in new tab..."
    
    # Normalize working directory path
    $WorkingDir = $WorkingDir.Trim('"').TrimEnd('\')
    
    # Create batch file for the service with color output
    $batFile = Join-Path $logDir "$ServiceName.bat"
    $batContent = @"
@echo off
chcp 65001 >nul
cd /d "$WorkingDir"
title $ServiceName
echo [%time%] [$ServiceName] Starting...
$Command
pause
"@
    Set-Content -Path $batFile -Value $batContent -Encoding UTF8
    
    # Method 1: Try using Tabby CLI if available (best method for same window)
    $tabbyCmd = Get-Command "tabby" -ErrorAction SilentlyContinue
    if ($tabbyCmd) {
        try {
            # Tabby CLI: create new tab in current window
            # Note: Tabby CLI syntax may vary, this is a common pattern
            $tabbyArgs = @(
                "new-tab",
                "--title", $TabName,
                "--command", "cmd.exe /c `"$batFile`""
            )
            Start-Process -FilePath "tabby" -ArgumentList $tabbyArgs -ErrorAction Stop
            Write-Success -Service "Tabby" -Message "Tab '$TabName' created via Tabby CLI"
            Start-Sleep -Seconds 1
            return
        } catch {
            Write-Warning -Service "Tabby" -Message "Tabby CLI method failed: $($_.Exception.Message)"
            Write-Info -Service "Tabby" -Message "Trying alternative method..."
        }
    }
    
    # Method 2: Use PowerShell with window title (Tabby groups by process/window)
    # This method works if Tabby is configured to group windows
    try {
        # Create PowerShell script that will start the service
        $psFile = Join-Path $logDir "$ServiceName.ps1"
        $psContent = @"
`$Host.UI.RawUI.WindowTitle = '$TabName'
Set-Location '$WorkingDir'
& cmd.exe /c '$batFile'
"@
        Set-Content -Path $psFile -Value $psContent -Encoding UTF8
        
        # Start new PowerShell window with specific window title
        # Tabby should group these in the same window if configured correctly
        $psArgs = @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$psFile`""
        )
        Start-Process -FilePath "powershell.exe" -ArgumentList $psArgs -ErrorAction Stop
        Write-Success -Service "Tabby" -Message "Started $ServiceName (Tabby should create tab in same window)"
        Start-Sleep -Seconds 1
    } catch {
        # Method 3: Fallback to regular cmd window
        Write-Warning -Service "Tabby" -Message "Using fallback method for $ServiceName..."
        Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "title $ServiceName && cd /d `"$WorkingDir`" && $Command"
    }
}

# Start services in tabs (all in ONE Tabby window)
Write-Info -Service "Tabby" -Message "Starting services in Tabby tabs (same window)..."

# IMPORTANT: Tab 1 must be Main Monitor (first tab)
# We'll start it first, then other services will be added as subsequent tabs
Write-Info -Service "Tabby" -Message "Starting Main Monitor as FIRST tab..."
$mainPsFile = Join-Path $logDir "main-monitor.ps1"
$mainPsContent = @"
`$Host.UI.RawUI.WindowTitle = 'Main Monitor - All Services'
Set-Location '$ProjectRoot'
& powershell.exe -ExecutionPolicy Bypass -File '$scriptPath\monitor-services.ps1' -ProjectRoot '$ProjectRoot'
"@
Set-Content -Path $mainPsFile -Value $mainPsContent -Encoding UTF8

# Start Main Monitor in new tab (will be first tab)
# Use Tabby CLI if available, otherwise PowerShell
$tabbyCmd = Get-Command "tabby" -ErrorAction SilentlyContinue
if ($tabbyCmd) {
    try {
        $tabbyArgs = @(
            "new-tab",
            "--title", "Main Monitor - All Services",
            "--command", "powershell.exe -NoExit -ExecutionPolicy Bypass -File `"$mainPsFile`""
        )
        Start-Process -FilePath "tabby" -ArgumentList $tabbyArgs -ErrorAction Stop
        Write-Success -Service "Tabby" -Message "Main Monitor tab created via Tabby CLI (first tab)"
    } catch {
        # Fallback to PowerShell
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$mainPsFile`"" -ErrorAction SilentlyContinue
        Write-Info -Service "Tabby" -Message "Main Monitor started (Tabby should create tab in same window)"
    }
} else {
    # No Tabby CLI, use PowerShell (Tabby will group if configured)
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$mainPsFile`"" -ErrorAction SilentlyContinue
    Write-Info -Service "Tabby" -Message "Main Monitor started (Tabby should create tab in same window)"
}
Start-Sleep -Seconds 2

# Tab 2: Chrome CDP (already started, just monitor)
Write-Info -Service "Tabby" -Message "Chrome CDP is already running (started separately)"

# Tab 3: Parser Service
Start-ServiceInTab -TabName "Parser Service" -ServiceName "Parser Service" -Command "parser_service\start-parser-service.bat" -WorkingDir $ProjectRoot
Start-Sleep -Seconds 1

# Tab 4: Backend
Start-ServiceInTab -TabName "Backend API" -ServiceName "Backend" -Command "start-backend.bat" -WorkingDir $ProjectRoot
Start-Sleep -Seconds 1

# Tab 5: Frontend
Start-ServiceInTab -TabName "Frontend" -ServiceName "Frontend" -Command "start-frontend.bat" -WorkingDir $ProjectRoot

Write-Host ""
Write-Success -Service "Tabby" -Message "All services started in Tabby terminal (same window)!"
Write-Host ""
Write-Host "Check the Tabby terminal tabs (in ONE window):" -ForegroundColor Cyan
Write-Host "  Tab 1: Main Monitor - All logs with colors" -ForegroundColor White
Write-Host "  Tab 2: Parser Service - Parser logs" -ForegroundColor White
Write-Host "  Tab 3: Backend API - Backend logs" -ForegroundColor White
Write-Host "  Tab 4: Frontend - Frontend logs" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: If tabs opened in separate windows:" -ForegroundColor Yellow
Write-Host "  1. Go to Tabby Settings → Window" -ForegroundColor Yellow
Write-Host "  2. Enable 'Open new tabs in the same window'" -ForegroundColor Yellow
Write-Host "  3. Restart Tabby and run this script again" -ForegroundColor Yellow
Write-Host ""

