---
title: "How-to: Интеграция Windows SMB шары для импорта"
type: how-to
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

## Цель
Подключить выгрузку файлов печати с Windows-сервера в watcher (`/app/data/watch`) через SMB (CIFS) с Linux-стороны (pull, read-only).

## Рекомендованный вариант: pull с Ubuntu (host) и bind-mount в watcher

1) Установить CIFS и создать точку монтирования
```bash
sudo apt-get update && sudo apt-get install -y cifs-utils
sudo mkdir -p /mnt/printshare
```

2) Смонтировать шару Windows (замените хост/шару/домен/логин)
```bash
sudo mount -t cifs //WIN-SERVER/PrintEvents /mnt/printshare \
  -o username=WIN_USER,password='WIN_PASS',domain=WIN_DOMAIN,vers=3.0,ro,iocharset=utf8
```

3) Привязать шару в watcher (compose)
В `docker-compose.yml` (или prod-оверлее) добавьте для сервиса `watcher`:
```yaml
services:
  watcher:
    volumes:
      - /mnt/printshare:/app/data/watch:ro
      - logs:/app/logs
      - data:/app/data
```

4) Перезапустить watcher
```bash
docker compose up -d watcher
docker compose exec watcher ls -la /app/data/watch
```

## Атомарность
- Выгружайте файл на Windows во временное имя (например, `.tmp`), затем делайте `Rename` в конечное имя — watcher увидит уже полностью записанный файл.

## Альтернативы
- SFTP/SSH (push с Windows): `pscp`/WinSCP в директорию `/var/lib/docker/volumes/<project>_data/_data/watch/` на Ubuntu.
- Samba на Ubuntu (share → Windows push): привычнее для AD, но открывает дополнительный сервис на Linux.
- Периодический `rsync` с `remove-source-files` в локальную watch-папку.

## Траблшутинг
- Права/доступ: проверьте, что монтирование `ro`, кодировка `iocharset=utf8` корректна.
- Логи демона: `docker compose logs watcher --tail=200`.
- Проверка путей: `docker volume inspect advisor-dj_data -f '{{.Mountpoint}}'`.


