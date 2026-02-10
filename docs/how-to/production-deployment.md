---
title: "Production Deployment"
type: guide
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Production Deployment

## 1) Settings profile

- Используйте `DJANGO_SETTINGS_MODULE=config.settings.production`.
- Убедитесь, что `DEBUG=0`.
- Заполните `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.

## 2) Secrets and env

- Секреты только через переменные окружения (`SECRET_KEY`, DB creds, токены).
- Не коммитьте `.env` в репозиторий.
- Для генерации базового env используйте `scripts/generate_env.sh`.

## 3) Database and migrations

```bash
docker compose exec web python manage.py migrate --noinput
```

## 4) Static files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

## 5) Reverse proxy / TLS

- Используйте `docker-compose.proxy.yml` и конфиги из `infrastructure/nginx/`.
- Для HTTPS см. `ENABLE_HTTPS.md` и `docs/WINDOWS_CA_CERTIFICATES.md`.

## 6) Post-deploy checks

```bash
curl -f http://localhost/health/
./scripts/smoke.sh
```

## 7) Operational docs

- `docs/DEPLOYMENT_CHECKLIST.md`
- `docs/DEPLOYMENT_READINESS.md`
- `docs/RUNBOOK.md`
