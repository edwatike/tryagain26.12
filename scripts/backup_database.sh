#!/bin/bash
# Script for backing up PostgreSQL database
# Usage: ./backup_database.sh [database_name] [backup_dir]

set -e

# Configuration
DB_NAME="${1:-b2b}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${2:-./backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${DATE}.sql"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
echo "Starting backup of database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "${BACKUP_FILE}.dump" || \
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $BACKUP_FILE"
    
    # Compress backup
    if command -v gzip &> /dev/null; then
        gzip "$BACKUP_FILE" 2>/dev/null || true
        echo "Backup compressed: ${BACKUP_FILE}.gz"
    fi
    
    # Keep only last 30 days of backups
    find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql*" -mtime +30 -delete 2>/dev/null || true
    echo "Old backups cleaned (kept last 30 days)"
else
    echo "Backup failed!"
    exit 1
fi

