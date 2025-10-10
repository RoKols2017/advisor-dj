---
title: "Runbook (Print Advisor)"
type: how-to
status: draft
last_verified: "2025-09-30"
owner: "@rom"
---

## Операционные процедуры

### 1. Запуск/остановка стека
```bash
docker compose up -d
docker compose down
docker compose ps
```

### 2. Миграции и статика
```bash
docker compose exec web python manage.py migrate --noinput
docker compose exec web python manage.py collectstatic --noinput
```

### 3. Health и smoke
```bash
curl -f http://localhost:8000/health/
./scripts/smoke.sh
```

### 3.1 Локальная проверка prod-профиля
- Для локальной проверки используйте прод‑оверлей и корректный Host:
```bash
docker compose -f docker-compose.prod.yml up -d
curl -H 'Host: printadvisor.local' -f http://localhost:8000/health/
```

### 4. Доступ в админку
```bash
docker compose exec -e DJANGO_SUPERUSER_PASSWORD='Strong!Pass' web \
  python manage.py createsuperuser --noinput --username admin --email you@domain.com
```

### 5. Импорт через демон
- Папки в контейнере watcher:
  - /app/data/watch (вход)
  - /app/data/processed (успех)
  - /app/data/quarantine (ошибки)

Положить файл:
```bash
docker cp ./events.json advisor-watcher:/app/data/watch/
docker compose logs watcher --tail=200
```

### 6. Логи
```bash
docker compose logs web --tail=200
docker compose logs watcher --tail=200
```

### 7. Бэкапы БД (пример)
```bash
docker compose exec db pg_dump -U ${POSTGRES_USER:-advisor} ${POSTGRES_DB:-advisor} > backup.sql
```

### 8. Rollback (кратко)
1) Откатиться на предыдущий тег образа в compose.
2) `docker compose pull && up -d`.
3) При необходимости откатить миграции: `python manage.py migrate <app> <migration>`.

### 9. Прод‑чеклист (кратко)
- Настройки prod активны; ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS корректны.
- Reverse‑proxy с TLS настроен; health 200 через HTTPS.
- Миграции применены; статика собрана.
- Watcher видит шары; quarantine/processed работают.
- Smoke зелёный; логи без ошибок; бэкапы настроены.

---
title: "Runbook"
type: guide
status: draft
last_verified: "2025-09-29"
verified_against_commit: "latest"
owner: "@rom"
---

# Runbook

- Setup: TBD
- Operations: TBD

