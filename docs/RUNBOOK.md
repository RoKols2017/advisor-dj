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
docker compose up -d
docker compose down
docker compose ps
```

Для стека с reverse proxy:

```bash
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.proxy.yml down
docker compose -f docker-compose.proxy.yml ps
```

## 2) Миграции и статика

```bash
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py collectstatic --noinput
```

## 3) Проверки health/smoke

```bash
curl -f http://localhost/health
./scripts/smoke.sh
```

Если используется reverse proxy:

```bash
curl -f http://localhost/health/
```

## 4) Доступ в админку

Создать суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

## 5) Импорт через watcher

Каталоги watcher в контейнере:
- `/app/data/watch` - входящие файлы
- `/app/data/processed` - успешно обработанные
- `/app/data/quarantine` - файлы с ошибками

Проверка импорта:

```bash
docker cp ./events.json advisor-watcher:/app/data/watch/
docker compose logs watcher --tail=200
```

## 6) Логи и диагностика

```bash
docker compose logs web --tail=200
docker compose logs watcher --tail=200
docker compose logs db --tail=200
```

Проверка Django:

```bash
docker compose exec web python manage.py check
```

## 7) Бэкап и восстановление БД

Бэкап:

```bash
docker compose exec db pg_dump -U ${POSTGRES_USER:-advisor} ${POSTGRES_DB:-advisor} > backup.sql
```

Восстановление:

```bash
cat backup.sql | docker compose exec -T db psql -U ${POSTGRES_USER:-advisor} ${POSTGRES_DB:-advisor}
```

## 8) Rollback

1. Вернуть предыдущий тег образов в compose.
2. Перезапустить стек (`docker compose pull && docker compose up -d`).
3. При необходимости откатить миграцию:

```bash
docker compose exec web python manage.py migrate <app_label> <migration_name>
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
