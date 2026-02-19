#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <backup.sql.gz|backup.sql> [target_db]"
    exit 1
fi

BACKUP_FILE="$1"
TARGET_DB="${2:-}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: backup file not found: $BACKUP_FILE"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: env file not found: $ENV_FILE"
    exit 1
fi

db_user="$(grep '^POSTGRES_USER=' "$ENV_FILE" | cut -d'=' -f2-)"
db_name="$(grep '^POSTGRES_DB=' "$ENV_FILE" | cut -d'=' -f2-)"

if [[ -z "$db_user" || -z "$db_name" ]]; then
    echo "ERROR: POSTGRES_USER/POSTGRES_DB are not set in $ENV_FILE"
    exit 1
fi

if [[ -z "$TARGET_DB" ]]; then
    TARGET_DB="$db_name"
fi

echo "Restoring into database: $TARGET_DB"

if [[ "$BACKUP_FILE" == *.gz ]]; then
    gzip -dc "$BACKUP_FILE" | docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db psql -U "$db_user" "$TARGET_DB"
else
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db psql -U "$db_user" "$TARGET_DB" < "$BACKUP_FILE"
fi

echo "Restore completed"
