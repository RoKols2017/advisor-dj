---
title: "Runbook (Print Advisor)"
type: guide
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

# Runbook

## 1) Управление стеком

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
docker compose --env-file .env.prod -f docker-compose.prod.yml down
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
```

Для стека с reverse proxy:

```bash
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.proxy.yml down
docker compose -f docker-compose.proxy.yml ps
```

## 2) Миграции и статика

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py migrate --noinput
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 3) Проверки health/smoke

```bash
curl -k -f https://localhost/health/
SMOKE_COMPOSE_FILE=docker-compose.prod.yml SMOKE_ENV_FILE=.env.prod ./scripts/smoke.sh
./scripts/check_stack_health.sh
```

Если используется reverse proxy:

```bash
curl -k -f https://localhost/health/
```

## 4) Доступ в админку

Создать суперпользователя:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## 5) Импорт через watcher

Каталоги watcher в контейнере:
- `/app/data/watch` - входящие файлы
- `/app/data/processed` - успешно обработанные
- `/app/data/quarantine` - файлы с ошибками

Проверка импорта:

```bash
docker cp ./events.json advisor-watcher:/app/data/watch/
docker compose --env-file .env.prod -f docker-compose.prod.yml logs watcher --tail=200
```

## 6) Логи и диагностика

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs web --tail=200
docker compose --env-file .env.prod -f docker-compose.prod.yml logs watcher --tail=200
docker compose --env-file .env.prod -f docker-compose.prod.yml logs db --tail=200
docker compose -f docker-compose.proxy.yml logs nginx --tail=200
```

Проверка Django:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py check --deploy
```

## 7) Бэкап и восстановление БД

Бэкап:

```bash
./scripts/backup_db.sh
```

Восстановление:

```bash
./scripts/restore_db.sh ./backups/advisor-db-YYYYmmdd-HHMMSS.sql.gz
```

Тестовый restore drill в отдельную БД:

```bash
DB_USER=$(grep '^POSTGRES_USER=' .env.prod | cut -d'=' -f2-)
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS advisor_restore_test;"
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE advisor_restore_test;"
./scripts/restore_db.sh ./backups/advisor-db-YYYYmmdd-HHMMSS.sql.gz advisor_restore_test
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE advisor_restore_test;"
```

Расписание backup (cron):

```bash
crontab infrastructure/cron/advisor-db-backup.cron
```

## 8) Rollback

1. Вернуть предыдущий тег образов в compose.
2. Перезапустить стек (`docker compose --env-file .env.prod -f docker-compose.prod.yml up -d`).
3. При необходимости откатить миграцию:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py migrate <app_label> <migration_name>
```

## 9) Операционный минимум перед релизом

- `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` корректны.
- Сервис `web` и `watcher` здоровы, `/health/` возвращает `200`.
- Миграции применены.
- Smoke-тест проходит.
- Логи без повторяющихся traceback.
- Бэкапы БД выполняются по расписанию.

## 10) Связанные документы

- `docs/DEPLOYMENT_CHECKLIST.md`
- `docs/DEPLOYMENT_READINESS.md`
- `docs/ENV.md`
- `docs/FILE_WATCHER_SETUP.md`
