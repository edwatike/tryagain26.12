@echo off
echo ========================================
echo   B2B Platform - Database Setup
echo ========================================
echo.
echo This script will apply migrations to your existing database.
echo.
set /p DB_NAME="Enter database name (default: postgres): "
if "%DB_NAME%"=="" set DB_NAME=postgres

set /p DB_USER="Enter database user (default: postgres): "
if "%DB_USER%"=="" set DB_USER=postgres

set /p DB_PASSWORD="Enter database password (default: postgres): "
if "%DB_PASSWORD%"=="" set DB_PASSWORD=postgres

set /p DB_HOST="Enter database host (default: localhost): "
if "%DB_HOST%"=="" set DB_HOST=localhost

set /p DB_PORT="Enter database port (default: 5432): "
if "%DB_PORT%"=="" set DB_PORT=5432

echo.
echo Applying migrations to database: %DB_NAME%
echo.

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f backend\migrations\001_initial_schema.sql

if errorlevel 1 (
    echo.
    echo ERROR: Failed to apply migrations!
    echo Please check your database credentials and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Database setup completed!
echo ========================================
echo.
echo Update your backend/.env file with:
echo DATABASE_URL=postgresql+asyncpg://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo.
pause

