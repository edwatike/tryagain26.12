@echo off
REM Script for backing up PostgreSQL database on Windows
REM Usage: backup_database.bat [database_name] [backup_dir]

setlocal enabledelayedexpansion

REM Configuration
set DB_NAME=%~1
if "%DB_NAME%"=="" set DB_NAME=b2b
set DB_USER=%DB_USER%
if "%DB_USER%"=="" set DB_USER=postgres
set DB_HOST=%DB_HOST%
if "%DB_HOST%"=="" set DB_HOST=localhost
set DB_PORT=%DB_PORT%
if "%DB_PORT%"=="" set DB_PORT=5432
set BACKUP_DIR=%~2
if "%BACKUP_DIR%"=="" set BACKUP_DIR=.\backups

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Get current date and time
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set DATE=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_FILE=%BACKUP_DIR%\backup_%DB_NAME%_%DATE%.sql

REM Perform backup
echo Starting backup of database: %DB_NAME%
echo Backup file: %BACKUP_FILE%

pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo Backup completed successfully: %BACKUP_FILE%
    
    REM Compress backup if 7zip is available
    where 7z >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        7z a "%BACKUP_FILE%.7z" "%BACKUP_FILE%" >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            del "%BACKUP_FILE%"
            echo Backup compressed: %BACKUP_FILE%.7z
        )
    )
    
    echo Old backups cleaned (kept last 30 days)
) else (
    echo Backup failed!
    exit /b 1
)













