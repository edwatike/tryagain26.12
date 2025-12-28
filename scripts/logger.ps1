# Color logging functions for Tabby terminal
# Usage: . .\scripts\logger.ps1

function Write-ServiceLog {
    param(
        [string]$Service,
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "ERROR", "WARNING")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = "[$timestamp] [$Service]"
    
    switch ($Level) {
        "ERROR" {
            Write-Host "$prefix $Message" -ForegroundColor Red
        }
        "SUCCESS" {
            Write-Host "$prefix $Message" -ForegroundColor Green
        }
        "WARNING" {
            Write-Host "$prefix $Message" -ForegroundColor Yellow
        }
        default {
            Write-Host "$prefix $Message" -ForegroundColor White
        }
    }
}

function Write-Success {
    param([string]$Service, [string]$Message)
    Write-ServiceLog -Service $Service -Message $Message -Level "SUCCESS"
}

function Write-Error {
    param([string]$Service, [string]$Message)
    Write-ServiceLog -Service $Service -Message $Message -Level "ERROR"
}

function Write-Info {
    param([string]$Service, [string]$Message)
    Write-ServiceLog -Service $Service -Message $Message -Level "INFO"
}

function Write-Warning {
    param([string]$Service, [string]$Message)
    Write-ServiceLog -Service $Service -Message $Message -Level "WARNING"
}

# Functions are available in the current scope after dot-sourcing this script
# No need for Export-ModuleMember (this is a script, not a module)

