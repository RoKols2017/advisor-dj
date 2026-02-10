---
title: "Docker Deployment"
type: guide
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Docker Deployment

## Stack

Основной стек (`docker-compose.yml`):
- `web` - Django/Gunicorn
- `watcher` - импорт JSON/CSV из директории
- `db` - PostgreSQL

Дополнительный proxy-стек (`docker-compose.proxy.yml`):
- `nginx` - reverse proxy

## Quick start

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate --noinput
docker compose ps
```

## Verify

```bash
curl -f http://localhost:8000/health/
./scripts/smoke.sh
```

## Logs

```bash
docker compose logs web --tail=200
docker compose logs watcher --tail=200
docker compose logs db --tail=200
```

## Reverse proxy mode

```bash
docker network create reverse-proxy-network || true
docker compose -f docker-compose.proxy.yml up -d
curl -f http://localhost/health/
```

## Stop and cleanup

```bash
docker compose down
docker compose -f docker-compose.proxy.yml down
```
