[← Deployment](deployment.md) · [Back to README](../README.md) · [Testing →](testing.md)

# Operations

## Базовые команды

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
docker compose --env-file .env.prod -f docker-compose.prod.yml down
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs web --tail=200
docker compose --env-file .env.prod -f docker-compose.prod.yml logs watcher --tail=200
```

## Миграции и статика

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py migrate --noinput
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Health и smoke

```bash
curl -f http://localhost/health
curl -f http://localhost/health/
SMOKE_COMPOSE_FILE=docker-compose.prod.yml SMOKE_ENV_FILE=.env.prod ./scripts/smoke.sh
```

## Watcher операции

- Каталоги watcher: `/app/data/watch`, `/app/data/processed`, `/app/data/quarantine`
- Для Windows источников используйте транзитную схему `inbox -> ingest -> watch`

Полезные команды:

```bash
docker compose logs watcher -f
./scripts/check_import_status.sh
sudo /opt/advisor-dj/scripts/setup_transit_ingest.sh /srv/advisor
systemctl status advisor-ingest-mover.timer --no-pager
```

## Backup и restore

```bash
./scripts/backup_db.sh
./scripts/restore_db.sh ./backups/advisor-db-YYYYmmdd-HHMMSS.sql.gz
```

## Детальные runbook документы

- Операционный runbook: `RUNBOOK.md`
- Настройка watcher: `FILE_WATCHER_SETUP.md`
- Транзитный ingest: `how-to/transit-ingest-pipeline.md`

## See Also

- [Deployment](deployment.md) - процедуры запуска и релиза
- [Testing](testing.md) - что гонять после изменений
- [Troubleshooting](troubleshooting.md) - диагностика инцидентов
