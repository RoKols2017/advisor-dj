---
title: "How-to: Интеграция Windows SMB шары для импорта"
type: how-to
status: draft
last_verified: "2026-02-20"
verified_against_commit: "latest"
owner: "@rom"
---

## Цель
Подключить выгрузку файлов с Windows серверов через SMB в транзитные каталоги Linux, затем переносить их в watcher через локальный ingest-процесс.

## Рекомендованный вариант: push в транзитные каталоги

1) Подготовить структуру каталогов:

```bash
sudo /opt/advisor-dj/scripts/setup_transit_ingest.sh /srv/advisor
```

2) На Linux открыть SMB доступ только к транзитным каталогам:
- `/srv/advisor/inbox/dc/incoming`
- `/srv/advisor/inbox/print1/incoming`
- `/srv/advisor/inbox/print2/incoming`

3) Использовать скрипты в `scripts/windows/` для отправки файлов из DC/print-серверов в эти каталоги.

4) На Linux ingest-процесс переносит файлы в watcher queue по таймеру:

```bash
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest.env.example /etc/default/advisor-ingest
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest-mover.service /etc/systemd/system/
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest-mover.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now advisor-ingest-mover.timer
```

## Атомарность
- Отправляйте файл на Linux во временное имя (`.part`), после копирования переименовывайте в итоговое.
- Ingest переносит файл в watcher тоже атомарно (`.part` -> rename).

## Альтернативы
- Pull через CIFS mount (Linux читает Windows share) допустим для одного источника, но сложнее масштабируется на 3 сервера.
- SFTP/SSH push допустим, если SMB запрещен политиками.

## Траблшутинг
- Проверка таймера ingest: `systemctl status advisor-ingest-mover.timer --no-pager`.
- Логи ingest: `tail -n 200 /srv/advisor/ingest/logs/ingest_mover.log`.
- Логи watcher: `docker compose --env-file .env.prod -f docker-compose.prod.yml logs watcher --tail=200`.

## См. также
- `docs/how-to/transit-ingest-pipeline.md`

