# Script to capture and format logs from a service
# Usage: .\scripts\capture-service-logs.ps1 -ServiceName "Backend" -ProcessId 12345

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [Parameter(Mandatory=$true)]
    [int]$ProcessId
)

# Load logger functions
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$scriptPath\logger.ps1"

# Monitor process output
$process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
if (-not $process) {
    Write-Error -Service $ServiceName -Message "Process $ProcessId not found"
    exit 1
}

Write-Info -Service $ServiceName -Message "Monitoring process $ProcessId ($($process.ProcessName))"

# Wait for process to exit and monitor
while (-not $process.HasExited) {
    Start-Sleep -Seconds 1
}

Write-Error -Service $ServiceName -Message "Process exited with code $($process.ExitCode)"





