# Скрипт мониторинга ошибок последовательностей PostgreSQL в логах Backend
# Ищет ошибки типа InsufficientPrivilegeError, sequence errors и т.д.

param(
    [string]$LogPath = "logs",
    [int]$TailLines = 1000,
    [switch]$Watch,
    [int]$WatchInterval = 30
)

$ErrorPatterns = @(
    "InsufficientPrivilegeError",
    "sequence.*error",
    "sequence.*permission",
    "domains_queue.*seq",
    "PendingRollbackError.*sequence",
    "ALTER SEQUENCE.*failed",
    "GRANT.*SEQUENCE.*failed"
)

function Search-LogErrors {
    param([string]$LogPath, [int]$TailLines)
    
    $foundErrors = @()
    
    # Найти все лог-файлы Backend
    $logFiles = Get-ChildItem -Path $LogPath -Filter "Backend-*.log" -ErrorAction SilentlyContinue | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -First 5
    
    if (-not $logFiles) {
        Write-Host "No Backend log files found in $LogPath" -ForegroundColor Yellow
        return $foundErrors
    }
    
    foreach ($logFile in $logFiles) {
        Write-Host "Checking $($logFile.Name)..." -ForegroundColor Cyan
        
        # Читать последние строки лога
        $logContent = Get-Content $logFile.FullName -Tail $TailLines -ErrorAction SilentlyContinue
        
        foreach ($line in $logContent) {
            foreach ($pattern in $ErrorPatterns) {
                if ($line -match $pattern) {
                    $foundErrors += @{
                        File = $logFile.Name
                        Line = $line
                        Pattern = $pattern
                    }
                }
            }
        }
    }
    
    return $foundErrors
}

function Display-Errors {
    param([array]$Errors)
    
    if ($Errors.Count -eq 0) {
        Write-Host "✅ No sequence errors found in logs" -ForegroundColor Green
        return
    }
    
    Write-Host "`n⚠️  Found $($Errors.Count) sequence-related error(s):" -ForegroundColor Yellow
    Write-Host "=" * 80
    
    $grouped = $Errors | Group-Object -Property File
    
    foreach ($group in $grouped) {
        Write-Host "`nFile: $($group.Name)" -ForegroundColor Cyan
        Write-Host "-" * 80
        
        foreach ($error in $group.Group) {
            Write-Host "  Pattern: $($error.Pattern)" -ForegroundColor Red
            Write-Host "  Line: $($error.Line)" -ForegroundColor Gray
            Write-Host ""
        }
    }
    
    Write-Host "=" * 80
    Write-Host "`n💡 Recommendations:" -ForegroundColor Yellow
    Write-Host "  1. Check if migration was applied correctly"
    Write-Host "  2. Run: .\scripts\check-sequences-after-migration.ps1 -TableName <table_name>"
    Write-Host "  3. Check: docs/TROUBLESHOOTING.md for solutions"
    Write-Host "  4. Verify sequence permissions in PostgreSQL"
}

# Основная логика
if ($Watch) {
    Write-Host "Monitoring sequence errors (press Ctrl+C to stop)..." -ForegroundColor Cyan
    Write-Host "Check interval: $WatchInterval seconds`n" -ForegroundColor Gray
    
    while ($true) {
        $errors = Search-LogErrors -LogPath $LogPath -TailLines $TailLines
        Display-Errors -Errors $errors
        
        if ($errors.Count -gt 0) {
            Write-Host "`n⏳ Waiting $WatchInterval seconds before next check...`n" -ForegroundColor Gray
        }
        
        Start-Sleep -Seconds $WatchInterval
    }
} else {
    Write-Host "Checking for sequence errors in Backend logs..." -ForegroundColor Cyan
    Write-Host "Log path: $LogPath" -ForegroundColor Gray
    Write-Host "Checking last $TailLines lines from each log file`n" -ForegroundColor Gray
    
    $errors = Search-LogErrors -LogPath $LogPath -TailLines $TailLines
    Display-Errors -Errors $errors
    
    if ($errors.Count -gt 0) {
        exit 1
    } else {
        exit 0
    }
}







