# Скрипт для проверки миграций на наличие переименования последовательностей и прав доступа
param(
    [Parameter(Mandatory=$true)]
    [string]$MigrationFile
)

if (-not (Test-Path $MigrationFile)) {
    Write-Error "Файл миграции не найден: $MigrationFile"
    exit 1
}

$content = Get-Content $MigrationFile -Raw
$issues = @()

# Проверить переименование последовательностей
if ($content -match "RENAME TO" -and $content -notmatch "ALTER SEQUENCE.*RENAME") {
    $issues += "❌ Миграция переименовывает таблицу, но не переименовывает последовательность"
    $issues += "   Добавьте: ALTER SEQUENCE old_name_id_seq RENAME TO new_name_id_seq;"
}

# Проверить права доступа на последовательности
if ($content -match "CREATE.*SERIAL|ALTER TABLE.*ADD.*SERIAL" -and $content -notmatch "GRANT.*SEQUENCE") {
    $issues += "❌ Миграция создает SERIAL поле, но не выдает права доступа на последовательность"
    $issues += "   Добавьте: GRANT ALL PRIVILEGES ON SEQUENCE sequence_name TO postgres;"
}

if ($issues.Count -gt 0) {
    Write-Error "Найдены проблемы в миграции $MigrationFile:"
    $issues | ForEach-Object { Write-Error "  $_" }
    exit 1
}

Write-Host "✅ Миграция $MigrationFile проверена успешно"
exit 0

