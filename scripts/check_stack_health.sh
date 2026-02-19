#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
HEALTH_URL="${HEALTH_URL:-https://localhost/health/}"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: env file not found: $ENV_FILE"
    exit 1
fi

echo "== Container status =="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" ps
docker compose -f docker-compose.proxy.yml ps

echo "== App health endpoint =="
curl -k -f -s "$HEALTH_URL"
echo

echo "== Watcher process =="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T watcher pgrep -f printing.print_events_watcher >/dev/null
echo "watcher is running"

echo "== Database ready =="
db_user="$(grep '^POSTGRES_USER=' "$ENV_FILE" | cut -d'=' -f2-)"
db_name="$(grep '^POSTGRES_DB=' "$ENV_FILE" | cut -d'=' -f2-)"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db pg_isready -U "$db_user" -d "$db_name"

echo "OK"
