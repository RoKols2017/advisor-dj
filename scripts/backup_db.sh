#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: env file not found: $ENV_FILE"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_file="$BACKUP_DIR/advisor-db-$timestamp.sql.gz"

db_user="$(grep '^POSTGRES_USER=' "$ENV_FILE" | cut -d'=' -f2-)"
db_name="$(grep '^POSTGRES_DB=' "$ENV_FILE" | cut -d'=' -f2-)"

if [[ -z "$db_user" || -z "$db_name" ]]; then
    echo "ERROR: POSTGRES_USER/POSTGRES_DB are not set in $ENV_FILE"
    exit 1
fi

echo "Creating backup: $backup_file"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U "$db_user" "$db_name" | gzip -c > "$backup_file"

echo "Backup created: $backup_file"

if [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
    find "$BACKUP_DIR" -type f -name 'advisor-db-*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
fi

echo "Done"
