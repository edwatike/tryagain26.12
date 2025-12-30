# Скрипт для быстрой проверки функциональности
# Использование: .\scripts\quick-check.ps1 [service]
# Параметры: backend, frontend, parser, all

param(
    [string]$Service = "all"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Check-Backend {
    Write-Host "`n=== Checking Backend ===" -ForegroundColor Cyan
    
    # Проверка импортов
    Write-Host "1. Checking imports..." -ForegroundColor Yellow
    python "$ProjectRoot\temp\backend\check_imports.py"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Imports OK" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Import errors found" -ForegroundColor Red
        return $false
    }
    
    # Проверка health endpoint
    Write-Host "2. Checking health endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ Backend is running" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ Backend returned status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️ Backend is not running or not accessible" -ForegroundColor Yellow
    }
    
    return $true
}

function Check-Frontend {
    Write-Host "`n=== Checking Frontend ===" -ForegroundColor Cyan
    
    Push-Location "$ProjectRoot\frontend\moderator-dashboard-ui"
    try {
        # Проверка линтера
        Write-Host "1. Checking linter..." -ForegroundColor Yellow
        $lintOutput = npm run lint 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Linter OK" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Linter errors found" -ForegroundColor Red
            Write-Host $lintOutput
            return $false
        }
        
        # Проверка доступности
        Write-Host "2. Checking availability..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host "   ✅ Frontend is running" -ForegroundColor Green
            }
        } catch {
            Write-Host "   ⚠️ Frontend is not running or not accessible" -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
    
    return $true
}

function Check-Parser {
    Write-Host "`n=== Checking Parser Service ===" -ForegroundColor Cyan
    
    # Проверка health endpoint
    Write-Host "1. Checking health endpoint..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:9003/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ Parser Service is running" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⚠️ Parser Service is not running or not accessible" -ForegroundColor Yellow
    }
    
    # Проверка Chrome CDP
    Write-Host "2. Checking Chrome CDP..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ Chrome CDP is running" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ⚠️ Chrome CDP is not running or not accessible" -ForegroundColor Yellow
    }
    
    return $true
}

# Главная логика
Write-Host "Quick Check Script" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan

$allPassed = $true

switch ($Service.ToLower()) {
    "backend" {
        $allPassed = Check-Backend
    }
    "frontend" {
        $allPassed = Check-Frontend
    }
    "parser" {
        $allPassed = Check-Parser
    }
    "all" {
        $backendOk = Check-Backend
        $frontendOk = Check-Frontend
        $parserOk = Check-Parser
        $allPassed = $backendOk -and $frontendOk -and $parserOk
    }
    default {
        Write-Host "Unknown service: $Service" -ForegroundColor Red
        Write-Host "Usage: .\scripts\quick-check.ps1 [backend|frontend|parser|all]" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`n===================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some checks failed!" -ForegroundColor Red
    exit 1
}





