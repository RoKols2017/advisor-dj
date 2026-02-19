---
title: "VM Deploy Commands"
type: guide
status: draft
last_verified: "2026-02-19"
verified_against_commit: "latest"
owner: "@rom"
---

# VM Deploy Commands

## Вариант 1: команды с комментариями

```bash
# 1) Перейти в каталог проекта на VM
cd /opt/advisor-dj

# 2) Проверить целостность офлайн-архива образов
sha256sum -c advisor-dj-images.tar.sha256

# 3) Загрузить Docker-образы из архива
docker load -i advisor-dj-images.tar

# 4) Создать сеть reverse-proxy (если уже есть, ошибки не будет)
docker network create reverse-proxy-network || true

# 5) Поднять production стек приложения
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d

# 6) Поднять Nginx reverse proxy
docker compose -f docker-compose.proxy.yml up -d

# 7) Применить миграции БД
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# 8) Проверить состояние контейнеров
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose -f docker-compose.proxy.yml ps

# 9) Проверить health endpoint по HTTPS (self-signed => -k)
curl -k -f https://localhost/health/

# 10) Прогнать операционный health-check
./scripts/check_stack_health.sh

# 11) Включить автозапуск через systemd
sudo cp advisor-dj.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service
sudo systemctl status advisor-dj.service --no-pager

# 12) Настроить ежедневный backup БД
crontab infrastructure/cron/advisor-db-backup.cron
crontab -l

# 13) Сделать ручной backup сразу после запуска
./scripts/backup_db.sh
```

## Вариант 2: команды без комментариев

```bash
cd /opt/advisor-dj
sha256sum -c advisor-dj-images.tar.sha256
docker load -i advisor-dj-images.tar
docker network create reverse-proxy-network || true
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d
docker compose -f docker-compose.proxy.yml up -d
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose -f docker-compose.proxy.yml ps
curl -k -f https://localhost/health/
./scripts/check_stack_health.sh
sudo cp advisor-dj.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service
sudo systemctl status advisor-dj.service --no-pager
crontab infrastructure/cron/advisor-db-backup.cron
crontab -l
./scripts/backup_db.sh
```

## Доступ в веб-интерфейс

- URL: `https://printadvisor.local/` или `https://<IP_VM>/`
- Текущий логин: `admin`
- Текущий пароль: `admin123`
- После входа обязательно сменить пароль.
