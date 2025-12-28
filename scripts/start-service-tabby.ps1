# Script to start a service in Tabby terminal with logging
# Usage: .\scripts\start-service-tabby.ps1 -ServiceName "Backend" -Command "start-backend.bat" -WorkingDir "D:\tryagain"

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(Mandatory=$true)]
    [string]$WorkingDir,
    
    [string]$LogFile = ""
)

# Load logger functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptPath\logger.ps1"

# Change to working directory
Set-Location $WorkingDir

# Create log file if specified
if ($LogFile -and $LogFile -ne "") {
    $logDir = Split-Path -Parent $LogFile
    if ($logDir -and -not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
}

# Function to parse and colorize log output
function Process-LogLine {
    param([string]$Line, [string]$Service)
    
    if ([string]::IsNullOrWhiteSpace($Line)) {
        return
    }
    
    # Detect error patterns
    if ($Line -match "(?i)(error|exception|failed|fail|critical|fatal)") {
        Write-Error -Service $Service -Message $Line
    }
    # Detect success patterns
    elseif ($Line -match "(?i)(success|ok|ready|started|running|listening)") {
        Write-Success -Service $Service -Message $Line
    }
    # Detect warning patterns
    elseif ($Line -match "(?i)(warning|warn|deprecated)") {
        Write-Warning -Service $Service -Message $Line
    }
    # Default info
    else {
        Write-Info -Service $Service -Message $Line
    }
}

# Start the service and capture output
Write-Info -Service $ServiceName -Message "Starting $ServiceName..."
Write-Info -Service $ServiceName -Message "Command: $Command"
Write-Info -Service $ServiceName -Message "Working directory: $WorkingDir"

try {
    # Start process and capture output
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $Command -NoNewWindow -PassThru -RedirectStandardOutput "nul" -RedirectStandardError "nul"
    
    # Wait a bit for initial output
    Start-Sleep -Seconds 2
    
    # Monitor process
    while (-not $process.HasExited) {
        Start-Sleep -Seconds 1
    }
    
    Write-Error -Service $ServiceName -Message "$ServiceName process exited with code $($process.ExitCode)"
} catch {
    Write-Error -Service $ServiceName -Message "Failed to start $ServiceName : $_"
}





