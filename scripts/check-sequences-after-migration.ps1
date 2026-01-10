# Скрипт для проверки последовательностей после применения миграции
param(
    [Parameter(Mandatory=$true)]
    [string]$TableName,
    [string]$DbPassword = "Jnvnszoe5971312059001",
    [string]$DbName = "b2bplatform",
    [string]$DbUser = "postgres",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432
)

$env:PGPASSWORD = $DbPassword

Write-Host "Проверка последовательностей для таблицы: $TableName" -ForegroundColor Cyan

# Получить все последовательности для таблицы
$query = "SELECT sequence_name FROM information_schema.sequences WHERE sequence_name LIKE '%${TableName}%';"
$sequences = psql -U $DbUser -d $DbName -h $DbHost -p $DbPort -t -c $query

$expectedName = "${TableName}_id_seq"
$found = $false
$fixed = $false

foreach ($seq in $sequences) {
    $seq = $seq.Trim()
    if ($seq) {
        Write-Host "  Найдена последовательность: $seq" -ForegroundColor Yellow
        
        if ($seq -eq $expectedName) {
            $found = $true
            Write-Host "  ✅ Имя последовательности корректно" -ForegroundColor Green
        } else {
            Write-Warning "  ⚠️ Неправильное имя последовательности: $seq (ожидается: $expectedName)"
            Write-Host "  Исправление..." -ForegroundColor Yellow
            $renameQuery = "ALTER SEQUENCE $seq RENAME TO $expectedName;"
            psql -U $DbUser -d $DbName -h $DbHost -p $DbPort -c $renameQuery | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Последовательность переименована" -ForegroundColor Green
                $fixed = $true
            } else {
                Write-Error "  ❌ Ошибка при переименовании последовательности"
            }
        }
        
        # Проверить права доступа
        $permissionsQuery = "\dp $expectedName"
        $permissions = psql -U $DbUser -d $DbName -h $DbHost -p $DbPort -c $permissionsQuery 2>&1
        if ($permissions -notmatch "postgres.*arwdDxt") {
            Write-Warning "  ⚠️ Последовательность $expectedName не имеет полных прав доступа"
            Write-Host "  Исправление..." -ForegroundColor Yellow
            $grantQuery = @"
GRANT ALL PRIVILEGES ON SEQUENCE $expectedName TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE $expectedName TO PUBLIC;
ALTER SEQUENCE $expectedName OWNER TO postgres;
"@
            psql -U $DbUser -d $DbName -h $DbHost -p $DbPort -c $grantQuery | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Права доступа исправлены" -ForegroundColor Green
                $fixed = $true
            } else {
                Write-Error "  ❌ Ошибка при выдаче прав доступа"
            }
        } else {
            Write-Host "  ✅ Права доступа корректны" -ForegroundColor Green
        }
    }
}

if (-not $found) {
    Write-Error "❌ Последовательность $expectedName не найдена!"
    exit 1
}

if ($fixed) {
    Write-Host "`n✅ Проверка завершена, проблемы исправлены" -ForegroundColor Green
} else {
    Write-Host "`n✅ Проверка завершена успешно, проблем не обнаружено" -ForegroundColor Green
}

exit 0













