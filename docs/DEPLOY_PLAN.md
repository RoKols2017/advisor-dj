---
title: "Deploy Plan (Print Advisor)"
type: guide
status: draft
last_verified: "2025-09-29"
verified_against_commit: "latest"
owner: "@rom"
---

## Сервисы

- web: Django + gunicorn + WhiteNoise
- watcher: `python -m printing.print_events_watcher`
- db: Postgres 15

## Переменные окружения (.env.example)

```env
DEBUG=0
SECRET_KEY=change-me
ALLOWED_HOSTS=example.com
DATABASE_URL=postgres://user:pass@db:5432/advisor
LOG_TO_FILE=1
LOG_TO_CONSOLE=0
LOG_DIR=/app/logs
PRINT_EVENTS_WATCH_DIR=/app/data/watch
PRINT_EVENTS_PROCESSED_DIR=/app/data/processed
ENABLE_WINDOWS_AUTH=0
```

## Процедура деплоя

```bash
docker compose build --no-cache
docker compose up -d db
sleep 5
docker compose up -d web watcher
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py collectstatic --noinput
docker compose ps
```

## Чеклист валидации продакшна

- `python manage.py check --deploy` без ошибок
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options
- Статика раздаётся WhiteNoise, без 404
- Логи пишутся в volume `logs/`
- Watcher видит `watch` каталог и перемещает файлы в `processed`

## Rollback

- Откатить на предыдущий образ; выполнить миграции в обратимом режиме при необходимости.

