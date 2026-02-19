---
title: "Go-Live Day Checklist"
type: guide
status: draft
last_verified: "2026-02-19"
verified_against_commit: "latest"
owner: "@rom"
---

# Go-Live Day Checklist

## 1) Pre-start

- [ ] На VM есть `docker`, `docker compose`, `systemd`.
- [ ] Подготовлены артефакты офлайн-пакета:
  - `advisor-dj-images.tar`
  - `advisor-dj-images.tar.sha256`
  - `images-manifest.txt`
  - `.env.prod`
- [ ] Проверена контрольная сумма:

```bash
sha256sum -c advisor-dj-images.tar.sha256
```

## 2) Deploy

- [ ] Загрузить образы:

```bash
docker load -i advisor-dj-images.tar
```

- [ ] Разместить `.env.prod` в `/opt/advisor-dj/.env.prod`.
- [ ] Поднять прод-контур:

```bash
cd /opt/advisor-dj
docker network create reverse-proxy-network || true
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
docker compose -f docker-compose.proxy.yml up -d
```

- [ ] Применить миграции:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
```

## 3) Acceptance

- [ ] Проверка состояния сервисов:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose -f docker-compose.proxy.yml ps
```

- [ ] Проверка health:

```bash
curl -k -f https://localhost/health/
```

- [ ] Проверка watcher и БД:

```bash
./scripts/check_stack_health.sh
```

- [ ] Проверка UI (login/admin/dashboard/statistics/tree) через браузер.

## 4) Operations

- [ ] Установить systemd unit:

```bash
sudo cp advisor-dj.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service
sudo systemctl status advisor-dj.service --no-pager
```

- [ ] Настроить backup по cron:

```bash
crontab infrastructure/cron/advisor-db-backup.cron
crontab -l
```

- [ ] Выполнить ручной backup:

```bash
./scripts/backup_db.sh
```

- [ ] Выполнить restore drill в тестовую БД:

```bash
LATEST_BACKUP=$(ls -1t backups/advisor-db-*.sql.gz | head -n 1)
DB_USER=$(grep '^POSTGRES_USER=' .env.prod | cut -d'=' -f2-)
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS advisor_restore_test;"
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE advisor_restore_test;"
./scripts/restore_db.sh "$LATEST_BACKUP" advisor_restore_test
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE advisor_restore_test;"
```

## 5) Post Go-Live

- [ ] Зафиксировать время запуска и версию релиза.
- [ ] Сохранить `.env.prod` и backup-артефакты в защищенном хранилище.
- [ ] Отдельной задачей заменить self-signed сертификат на доверенный.
