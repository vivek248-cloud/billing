#!/bin/bash

# === CONFIGURATION ===
DB_NAME="billingdb"
DB_USER="billinguser"
DB_PASSWORD="Admin123"
BACKUP_DIR="/var/backups/edb"
DATE=$(date +"%Y-%m-%d_%H-%M")
FILENAME="edbbilling_backup_$DATE.sql.gz"

# === RUN BACKUP ===
mkdir -p $BACKUP_DIR
PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h 127.0.0.1 -p 5432 $DB_NAME | gzip > "$BACKUP_DIR/$FILENAME"

# === DELETE backups older than 30 days ===
find "$BACKUP_DIR" -type f -name "*.sql.gz" | while read file; do
    
    file_date=$(basename "$file" | cut -d'_' -f3)  # extract YYYY-MM-DD
    
    file_ts=$(date -d "$file_date" +%s 2>/dev/null)
    cutoff_ts=$(date -d "30 days ago" +%s)

    if [[ $file_ts -lt $cutoff_ts ]]; then
        echo "Deleting old backup: $file"
        rm -f "$file"
    fi

done