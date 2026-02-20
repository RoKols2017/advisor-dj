---
title: "How-to: Транзитная загрузка из 3 Windows серверов"
type: how-to
status: draft
last_verified: "2026-02-20"
verified_against_commit: "latest"
owner: "@rom"
---

## Цель

Организовать безопасную и надежную загрузку файлов из трех источников:
- `dc` (CSV пользователей)
- `print1` (JSON событий печати)
- `print2` (JSON событий печати)

Принцип: Windows серверы пишут в транзитные каталоги, а локальный ingest-процесс переносит файлы в очередь watcher.

## Почему не писать напрямую в Docker volume

- Внутренние пути Docker (`/var/lib/docker/volumes/...`) считаются служебными.
- Прямая запись извне повышает риск повреждения данных и гонок при обработке.
- Транзитная зона позволяет валидировать, логировать, дедуплицировать и архивировать файлы до передачи watcher.

## 1) Подготовка каталогов на Linux

```bash
sudo /opt/advisor-dj/scripts/setup_transit_ingest.sh /srv/advisor
```

Будут созданы каталоги:
- `/srv/advisor/inbox/dc/incoming`
- `/srv/advisor/inbox/print1/incoming`
- `/srv/advisor/inbox/print2/incoming`
- `/srv/advisor/inbox/_failed`
- `/srv/advisor/inbox/_archive`
- `/srv/advisor/ingest/logs`
- `/srv/advisor/ingest/state`

## 2) Настройка точки назначения watcher

Вариант A (быстрый): оставить текущий volume-путь как целевой для ingest:
- `/var/lib/docker/volumes/advisor-dj_data/_data/watch`

Вариант B (рекомендуемый): переключить `web/watcher` на bind-mount `data` с хоста (например, `/srv/advisor/data`) и использовать `/srv/advisor/data/watch` как `WATCH_DIR`.

## 3) Настройка SMB endpoint на Linux

Рекомендуется создать 3 отдельных SMB share (или 3 пути в одном share):
- `advisor-dc$` -> `/srv/advisor/inbox/dc`
- `advisor-print1$` -> `/srv/advisor/inbox/print1`
- `advisor-print2$` -> `/srv/advisor/inbox/print2`

Требования:
- отдельная учетная запись на каждый источник;
- доступ только к своей папке;
- ограничение доступа по IP источника в firewall.

Пример шаблона Samba:
- `infrastructure/samba/smb.conf.example`

Минимальная установка Samba:

```bash
sudo apt-get update && sudo apt-get install -y samba
sudo cp /opt/advisor-dj/infrastructure/samba/smb.conf.example /etc/samba/smb.conf
sudo systemctl restart smbd
sudo systemctl enable smbd
```

Создание SMB пользователей:

```bash
sudo useradd -M -s /usr/sbin/nologin ingest_dc || true
sudo useradd -M -s /usr/sbin/nologin ingest_print1 || true
sudo useradd -M -s /usr/sbin/nologin ingest_print2 || true
sudo smbpasswd -a ingest_dc
sudo smbpasswd -a ingest_print1
sudo smbpasswd -a ingest_print2
sudo smbpasswd -e ingest_dc
sudo smbpasswd -e ingest_print1
sudo smbpasswd -e ingest_print2
```

Проверка и безопасное применение конфигурации:

```bash
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak.$(date +%F-%H%M%S)
sudo cp /opt/advisor-dj/infrastructure/samba/smb.conf.example /etc/samba/smb.conf
sudo testparm -s
sudo systemctl restart smbd
sudo systemctl enable smbd
```

Проверка доступа к share:

```bash
smbclient -L //localhost -U ingest_dc
smbclient //localhost/advisor-dc$ -U ingest_dc -c "ls"
smbclient //localhost/advisor-print1$ -U ingest_print1 -c "ls"
smbclient //localhost/advisor-print2$ -U ingest_print2 -c "ls"
```

Пример ограничения firewall (UFW) только для 3 источников:

```bash
sudo ufw allow from <DC_IP> to any port 445 proto tcp
sudo ufw allow from <PRINT1_IP> to any port 445 proto tcp
sudo ufw allow from <PRINT2_IP> to any port 445 proto tcp
sudo ufw status
```

## 4) Настройка ingest-процесса (Linux)

1. Создать env-файл:

```bash
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest.env.example /etc/default/advisor-ingest
sudo chmod 600 /etc/default/advisor-ingest
```

2. Проверить значения в `/etc/default/advisor-ingest`:
- `INBOX_ROOT=/srv/advisor/inbox`
- `WATCH_DIR=<путь к watch-очереди>`

3. Установить systemd unit/timer:

```bash
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest-mover.service /etc/systemd/system/
sudo cp /opt/advisor-dj/infrastructure/systemd/advisor-ingest-mover.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now advisor-ingest-mover.timer
```

4. Проверить запуск:

```bash
systemctl status advisor-ingest-mover.timer --no-pager
systemctl list-timers advisor-ingest-mover.timer --no-pager
journalctl -u advisor-ingest-mover.service -n 50 --no-pager
tail -n 50 /srv/advisor/ingest/logs/ingest_mover.log
```

## 5) Скрипты отправки на Windows

Готовые примеры находятся в `scripts/windows/`:
- `scripts/windows/send_dc_users.ps1`
- `scripts/windows/send_print1_events.ps1`
- `scripts/windows/send_print2_events.ps1`

Базовый скрипт:
- `scripts/windows/send_to_advisor_inbox.ps1`

Важно:
- Файл отправляется как `.part`, затем выполняется rename в конечное имя (атомарная загрузка).
- Имена файлов префиксуются `sourceId` и timestamp.

## 6) Task Scheduler на Windows

Рекомендуемые расписания:
- `dc`: каждые 15 минут
- `print1` и `print2`: каждые 5 минут

Учетная запись задачи должна иметь доступ к исходному каталогу и SMB-share назначения.

## 7) Операционные проверки

1. В транзитных каталогах появляются новые файлы:

```bash
ls -la /srv/advisor/inbox/dc/incoming
ls -la /srv/advisor/inbox/print1/incoming
ls -la /srv/advisor/inbox/print2/incoming
```

2. Ingest переносит файлы в очередь watcher:

```bash
ls -la /var/lib/docker/volumes/advisor-dj_data/_data/watch
tail -n 100 /srv/advisor/ingest/logs/ingest_mover.log
```

3. Watcher обрабатывает файлы:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs watcher --tail=200
```

## 8) Политика хранения и очистка

- Архивировать успешно переданные файлы в `/srv/advisor/inbox/_archive`.
- Ошибочные файлы складывать в `/srv/advisor/inbox/_failed`.
- Настроить `logrotate` для `/srv/advisor/ingest/logs/ingest_mover.log`.
- Регламент retention:
  - `_archive`: 14-30 дней
  - `_failed`: 30-90 дней

## 9) Минимальный план поэтапного запуска

1. Включить только `dc`, наблюдать 2-3 дня.
2. Подключить `print1`.
3. Подключить `print2`.
4. После стабилизации включить алерты по backlog и ошибкам.
