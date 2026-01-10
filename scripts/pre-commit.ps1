# Pre-commit hook для автоматических проверок
# Использование: Скопируйте в .git/hooks/pre-commit (или создайте симлинк)
# Для Windows: powershell.exe -ExecutionPolicy Bypass -File scripts/pre-commit.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "Running pre-commit checks..." -ForegroundColor Cyan

# 1. Проверка импортов Backend
Write-Host "`n1. Checking Backend imports..." -ForegroundColor Yellow
$importCheck = python "$ProjectRoot\temp\backend\check_imports.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend import check failed!" -ForegroundColor Red
    Write-Host "Fix import errors before committing." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backend imports OK" -ForegroundColor Green

# 2. Проверка линтера Frontend
Write-Host "`n2. Checking Frontend linter..." -ForegroundColor Yellow
Push-Location "$ProjectRoot\frontend\moderator-dashboard-ui"
try {
    $lintCheck = npm run lint 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend linter check failed!" -ForegroundColor Red
        Write-Host $lintCheck
        Write-Host "Fix linter errors before committing." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Frontend linter OK" -ForegroundColor Green
} finally {
    Pop-Location
}

# 3. Проверка сборки Frontend (опционально, можно закомментировать для ускорения)
# Write-Host "`n3. Checking Frontend build..." -ForegroundColor Yellow
# Push-Location "$ProjectRoot\frontend\moderator-dashboard-ui"
# try {
#     $buildCheck = npm run build 2>&1
#     if ($LASTEXITCODE -ne 0) {
#         Write-Host "❌ Frontend build failed!" -ForegroundColor Red
#         Write-Host $buildCheck
#         Write-Host "Fix build errors before committing." -ForegroundColor Red
#         exit 1
#     }
#     Write-Host "✅ Frontend build OK" -ForegroundColor Green
# } finally {
#     Pop-Location
# }

Write-Host "`n✅ All pre-commit checks passed!" -ForegroundColor Green
exit 0











