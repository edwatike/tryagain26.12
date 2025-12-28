# Script to start all services in ONE Tabby window with unified logging
# Usage: .\scripts\start-all-services-single-window.ps1 -ProjectRoot "D:\tryagain" [-Mode "debug"|"production"]
# This script runs all services and shows their logs in ONE window
# 
# Modes:
#   debug (default) - Detailed logging, faster monitoring (2-2.5s intervals)
#   production - Optimized for long-running, less verbose (3-5s intervals, only important messages after stabilization)

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("debug", "production")]
    [string]$Mode = "debug"
)

# Normalize path
$ProjectRoot = $ProjectRoot.Trim('"').TrimEnd('\')

# Load logger functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptPath\logger.ps1"

# Change to project root
Set-Location $ProjectRoot

# Set window title
$Host.UI.RawUI.WindowTitle = "Main Monitor - All Services"

Clear-Host

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  B2B Platform - All Services" -ForegroundColor Cyan
Write-Host "  Single Window Mode" -ForegroundColor Cyan
Write-Host "  Mode: $Mode" -ForegroundColor $(if ($Mode -eq "production") { "Yellow" } else { "Green" })
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create log directory
$logDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Store service processes and log files
$services = @{}

# Function to start service and capture output to log file
function Start-ServiceBackground {
    param(
        [string]$ServiceName,
        [string]$Command,
        [string]$WorkingDir
    )
    
    Write-Info -Service $ServiceName -Message "Starting $ServiceName..."
    
    # Create log file for this service with timestamp to avoid conflicts
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logFile = Join-Path $logDir "$ServiceName-$timestamp.log"
    
    # OPTIMIZATION: Clean up old log files (keep only last 5 per service)
    try {
        $oldLogs = Get-ChildItem -Path $logDir -Filter "$ServiceName-*.log" -ErrorAction SilentlyContinue | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -Skip 5
        if ($oldLogs) {
            $oldLogs | Remove-Item -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Ignore cleanup errors
    }
    
    # Create new log file
    try {
        New-Item -ItemType File -Path $logFile -Force -ErrorAction Stop | Out-Null
    } catch {
        Write-Error -Service $ServiceName -Message "Failed to create log file: $($_.Exception.Message)"
        return
    }
    
    # Resolve command to full path if it's relative
    if (-not [System.IO.Path]::IsPathRooted($Command)) {
        $Command = Join-Path $WorkingDir $Command
    }
    
    # Command should now be a full path, but verify
    if (-not (Test-Path $Command)) {
        Write-Error -Service $ServiceName -Message "Command not found: $Command"
        return
    }
    
    # Create a wrapper batch file without 'pause' for background execution
    $wrapperBat = Join-Path $logDir "$ServiceName-wrapper.bat"
    try {
        $batContent = Get-Content $Command -Raw -ErrorAction Stop
        if ($batContent) {
            # Remove 'pause' commands (case insensitive)
            # Remove lines that contain ONLY 'pause' (with optional whitespace) - whole line
            $batContent = $batContent -replace "(?m)^\s*pause\s*$", ""
            # Remove 'pause' at end of line (with optional whitespace before it)
            $batContent = $batContent -replace "(?m)\s+pause\s*$", ""
            # Remove standalone 'pause' followed by newline
            $batContent = $batContent -replace "(?m)^pause\s*\r?\n", ""
            
            # Remove trailing empty lines
            $batContent = $batContent.TrimEnd()
            
            # IMPORTANT: Replace %~dp0 with actual command directory path
            # Extract the directory from the original command (now full path)
            $cmdDir = Split-Path -Parent $Command
            Write-Info -Service $ServiceName -Message "Command: $Command, Replacing %~dp0 with: $cmdDir"
            
            # Replace %~dp0 using line-by-line processing for better control
            $lines = $batContent -split "`r?`n"
            $newLines = @()
            foreach ($line in $lines) {
                # Check if line contains %~dp0 followed by a path component
                if ($line -match '%~dp0([a-zA-Z][a-zA-Z0-9_]*)') {
                    $subdir = $matches[1]
                    # Replace %~dp0subdir with $cmdDir\subdir
                    $line = $line.Replace("%~dp0$subdir", "$cmdDir\$subdir")
                }
                # Replace any remaining standalone %~dp0
                $line = $line.Replace('%~dp0', "$cmdDir\")
                $newLines += $line
            }
            $batContent = $newLines -join "`r`n"
            
            # Ensure proper line endings (CRLF for batch files)
            $batContent = $batContent -replace "`r?`n", "`r`n"
            
            # Write wrapper batch file using .NET method for proper encoding
            [System.IO.File]::WriteAllText($wrapperBat, $batContent, [System.Text.Encoding]::ASCII)
            
            Write-Info -Service $ServiceName -Message "Created wrapper: $wrapperBat"
        } else {
            # If we can't read the original, create a simple wrapper
            # Extract directory from command path if it's a batch file
            $cmdDir = Split-Path -Parent $Command
            $wrapperContent = "@echo off`r`ncd /d `"$cmdDir`"`r`ncall `"$Command`"`r`n"
            [System.IO.File]::WriteAllText($wrapperBat, $wrapperContent, [System.Text.Encoding]::ASCII)
        }
    } catch {
        # If we can't read the original, create a simple wrapper
        # Extract directory from command path if it's a batch file
        $cmdDir = Split-Path -Parent $Command
        $wrapperContent = "@echo off`r`ncd /d `"$cmdDir`"`r`ncall `"$Command`"`r`n"
        [System.IO.File]::WriteAllText($wrapperBat, $wrapperContent, [System.Text.Encoding]::ASCII)
        Write-Warning -Service $ServiceName -Message "Could not read original batch file, created simple wrapper"
    }
    
    # Verify wrapper file was created and doesn't contain pause
    if (Test-Path $wrapperBat) {
        $wrapperContent = Get-Content $wrapperBat -Raw -ErrorAction SilentlyContinue
        if ($wrapperContent -and $wrapperContent -match "(?i)\bpause\b") {
            Write-Warning -Service $ServiceName -Message "Wrapper file still contains 'pause', attempting to remove..."
            $wrapperContent = $wrapperContent -replace "(?m)^\s*pause\s*$", "" -replace "(?m)\s+pause\s*$", "" -replace "(?m)^pause\s*\r?\n", ""
            $wrapperContent = $wrapperContent.TrimEnd() -replace "`r?`n", "`r`n"
            [System.IO.File]::WriteAllText($wrapperBat, $wrapperContent, [System.Text.Encoding]::ASCII)
        }
    }
    
    # Start process in background
    # Create a launcher batch file that will run the wrapper and redirect output
    $launcherBat = Join-Path $logDir "$ServiceName-launcher.bat"
    $launcherContent = "@echo off`r`ncd /d `"$WorkingDir`"`r`ncall `"$wrapperBat`" >> `"$logFile`" 2>&1`r`n"
    [System.IO.File]::WriteAllText($launcherBat, $launcherContent, [System.Text.Encoding]::ASCII)
    
    try {
        # Use ProcessStartInfo for better control
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "cmd.exe"
        $psi.Arguments = "/c `"$launcherBat`""
        $psi.WorkingDirectory = $WorkingDir
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        $process.Start() | Out-Null
        
        # Wait a moment to ensure process started
        Start-Sleep -Milliseconds 500
        
        # Verify process is still running
        if (-not $process.HasExited) {
            $services[$ServiceName] = @{
                Process = $process
                LogFile = $logFile
                LastPosition = 0  # Track file size instead of line count for better performance
                Name = $ServiceName
                StartTime = Get-Date
            }
            
            Write-Success -Service $ServiceName -Message "Started (PID: $($process.Id), Log: $logFile)"
        } else {
            Write-Error -Service $ServiceName -Message "Process exited immediately with code $($process.ExitCode)"
            # Try to read log to see what happened
            if (Test-Path $logFile) {
                Start-Sleep -Milliseconds 500
                $logContent = Get-Content $logFile -ErrorAction SilentlyContinue -TotalCount 10
                if ($logContent) {
                    Write-Info -Service $ServiceName -Message "Log: $($logContent -join ' | ')"
                } else {
                    Write-Info -Service $ServiceName -Message "Log file is empty"
                }
            }
        }
        Start-Sleep -Seconds 1
    } catch {
        Write-Error -Service $ServiceName -Message "Failed to start: $($_.Exception.Message)"
    }
}

# Start all services
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Parser Service
Start-ServiceBackground -ServiceName "Parser Service" -Command "parser_service\start-parser-service.bat" -WorkingDir $ProjectRoot

# Start Backend
Start-ServiceBackground -ServiceName "Backend" -Command "start-backend.bat" -WorkingDir $ProjectRoot

# Start Frontend
Start-ServiceBackground -ServiceName "Frontend" -Command "start-frontend.bat" -WorkingDir $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Services Started" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to read and display new log lines (OPTIMIZED)
function Read-ServiceLogs {
    foreach ($serviceName in $services.Keys) {
        $service = $services[$serviceName]
        $logFile = $service.LogFile
        
        if (Test-Path $logFile) {
            try {
                # OPTIMIZATION: Use -Tail to read only new lines instead of entire file
                # This is much more efficient for large log files
                $fileInfo = Get-Item $logFile -ErrorAction SilentlyContinue
                if ($fileInfo) {
                    $currentSize = $fileInfo.Length
                    
                    # Only read if file has grown (more efficient than reading entire file)
                    if ($currentSize -gt $service.LastPosition) {
                        try {
                            # Read only new content using -Tail with estimated line count
                            # Calculate approximate number of new lines (assuming ~80 chars per line)
                            $estimatedNewLines = [math]::Max(1, [math]::Floor(($currentSize - $service.LastPosition) / 80))
                            # Limit based on mode: debug shows more, production shows less
                            $maxLines = if ($Mode -eq "production") { 50 } else { 100 }
                            $linesToRead = [math]::Min($maxLines, $estimatedNewLines)
                            
                            # Read new lines from the end
                            $newLines = Get-Content $logFile -Tail $linesToRead -ErrorAction SilentlyContinue
                            
                            if ($newLines) {
                                # Process new lines (using -Tail ensures we get the latest content)
                                foreach ($line in $newLines) {
                                    if ($line -and $line.Trim()) {
                                        # Skip pause-related messages
                                        if ($line -match "(?i)(press any key|pause|для продолжения)") {
                                            continue
                                        }
                                        
                                        # In production mode after stabilization: only show errors, warnings, and critical success messages
                                        if ($Mode -eq "production" -and $servicesStable) {
                                            # Skip verbose info messages in production
                                            if ($line -match "(?i)(error|exception|failed|fail|critical|fatal|warning|warn)") {
                                                # Show errors and warnings
                                                if ($line -match "(?i)(error|exception|failed|fail|critical|fatal)") {
                                                    Write-Error -Service $serviceName -Message $line
                                                } elseif ($line -match "(?i)(warning|warn)") {
                                                    Write-Warning -Service $serviceName -Message $line
                                                }
                                            } elseif ($line -match "(?i)(success|ok|ready|started|running|listening)") {
                                                # Show only critical startup messages
                                                Write-Success -Service $serviceName -Message $line
                                            }
                                            # Skip all other messages in production mode
                                            continue
                                        }
                                        
                                        # Colorize output based on patterns (full logging in debug mode)
                                        if ($line -match "(?i)(error|exception|failed|fail|critical|fatal)") {
                                            Write-Error -Service $serviceName -Message $line
                                        } elseif ($line -match "(?i)(success|ok|ready|started|running|listening|ready in|uvicorn running|application startup|hypercorn|running on)") {
                                            Write-Success -Service $serviceName -Message $line
                                        } elseif ($line -match "(?i)(warning|warn|notice)") {
                                            Write-Warning -Service $serviceName -Message $line
                                        } else {
                                            Write-Info -Service $serviceName -Message $line
                                        }
                                    }
                                }
                                
                                # Update last position to current file size
                                $service.LastPosition = $currentSize
                            }
                        } catch {
                            # If -Tail fails (e.g., file locked), fall back to tracking by size
                            $service.LastPosition = $currentSize
                        }
                    }
                }
            } catch {
                # Log file might be locked, skip this iteration
            }
        }
        
        # Check if process is still running
        if ($service.Process.HasExited) {
            $exitCode = $service.Process.ExitCode
            if ($exitCode -ne 0) {
                Write-Error -Service $serviceName -Message "Service exited with code $exitCode"
                # Try to read any remaining log content
                if (Test-Path $logFile) {
                    try {
                        $remaining = Get-Content $logFile -Tail 5 -ErrorAction SilentlyContinue
                        foreach ($line in $remaining) {
                            if ($line) {
                                Write-Info -Service $serviceName -Message $line
                            }
                        }
                    } catch {}
                }
            }
        }
    }
}

# Health check function
function Check-ServicesHealth {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Health Check" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check Chrome CDP
    $chromePort = Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue
    if ($chromePort) {
        Write-Success -Service "Chrome CDP" -Message "Port 9222 is listening"
    } else {
        Write-Error -Service "Chrome CDP" -Message "Port 9222 is not listening"
    }
    
    # Check Parser Service
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:9003/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success -Service "Parser Service" -Message "Running on http://127.0.0.1:9003"
        }
    } catch {
        Write-Error -Service "Parser Service" -Message "Not responding on http://127.0.0.1:9003"
    }
    
    # Check Backend
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success -Service "Backend" -Message "Running on http://127.0.0.1:8000"
        }
    } catch {
        Write-Error -Service "Backend" -Message "Not responding on http://127.0.0.1:8000"
    }
    
    # Check Frontend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Success -Service "Frontend" -Message "Running on http://localhost:3000"
        }
    } catch {
        Write-Error -Service "Frontend" -Message "Not responding on http://localhost:3000"
    }
    
    Write-Host ""
}

# Initial health check
Start-Sleep -Seconds 5
Check-ServicesHealth

# Continuous monitoring
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Continuous Monitoring" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info -Service "Monitor" -Message "Monitoring services... Press Ctrl+C to stop"
Write-Host ""

$iteration = 0
$servicesStable = $false
$stableIterations = 0

# Configure intervals based on mode
$monitorInterval = if ($Mode -eq "production") { 3.5 } else { 2 }
$monitorIntervalStable = if ($Mode -eq "production") { 5 } else { 2.5 }
$healthCheckIntervalStartup = if ($Mode -eq "production") { 20 } else { 15 }  # iterations
$healthCheckIntervalStable = if ($Mode -eq "production") { 40 } else { 30 }  # iterations

Write-Info -Service "Monitor" -Message "Monitoring interval: $monitorInterval seconds (startup), $monitorIntervalStable seconds (stable)"
Write-Info -Service "Monitor" -Message "Health check interval: $($healthCheckIntervalStartup * $monitorInterval) seconds (startup), $($healthCheckIntervalStable * $monitorIntervalStable) seconds (stable)"
Write-Host ""

while ($true) {
    $iteration++
    
    # Read and display new log lines from all services
    Read-ServiceLogs
    
    # Health check frequency based on mode:
    # Debug mode: Every 30 seconds during startup, 60 seconds after stable
    # Production mode: Every 70 seconds during startup, 200 seconds (3.3 min) after stable
    if (-not $servicesStable) {
        # During startup phase
        if ($iteration % $healthCheckIntervalStartup -eq 0) {
            Check-ServicesHealth
            # Check if all services are running
            $allRunning = $true
            foreach ($serviceName in $services.Keys) {
                if ($services[$serviceName].Process.HasExited) {
                    $allRunning = $false
                    break
                }
            }
            if ($allRunning) {
                $stableIterations++
                # After 3 successful checks, consider services stable
                $requiredChecks = if ($Mode -eq "production") { 2 } else { 3 }
                if ($stableIterations -ge $requiredChecks) {
                    $servicesStable = $true
                    $checkInterval = $healthCheckIntervalStable * $monitorIntervalStable
                    Write-Info -Service "Monitor" -Message "Services are stable. Health checks reduced to every $checkInterval seconds."
                    if ($Mode -eq "production") {
                        Write-Info -Service "Monitor" -Message "Production mode: Showing only errors, warnings, and critical messages."
                    }
                }
            }
        }
    } else {
        # After stabilization: less frequent health checks
        if ($iteration % $healthCheckIntervalStable -eq 0) {
            Check-ServicesHealth
        }
    }
    
    # Sleep interval based on mode and stability
    if ($servicesStable) {
        Start-Sleep -Seconds $monitorIntervalStable
    } else {
        Start-Sleep -Seconds $monitorInterval
    }
}
