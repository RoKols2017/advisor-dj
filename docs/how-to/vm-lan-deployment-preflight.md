---
title: "VM Deployment Pre-Flight and LAN Cutover Plan"
type: guide
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

# VM Deployment Pre-Flight and LAN Cutover Plan

План для сценария:
1) поднять проект на виртуальном сервере с доступом в интернет;
2) выполнить настройку и проверку;
3) перевести сервер в закрытую внутреннюю ЛВС.

## 1. Pre-Flight (до начала развертывания)

### 1.1 Данные и ответственность
- [ ] Зафиксирован целевой внутренний адрес: `FQDN` и/или IP.
- [ ] Назначены ответственные: деплой, сеть, приемка, откат.
- [ ] Согласовано окно работ (start/end) и критерии `go/no-go`.

### 1.2 Доступы и инфраструктура
- [ ] Есть SSH-доступ и `sudo` на VM.
- [ ] Установлены Docker и Docker Compose.
- [ ] Доступен репозиторий (или архив проекта).
- [ ] Есть место на диске под `pgdata`, `logs`, `data/*`.

### 1.3 Конфиг и секреты
- [ ] Подготовлен `.env.prod` (не хранить секреты в git).
- [ ] Установлены значения: `DEBUG=0`, `ALLOWED_HOSTS`, `SECRET_KEY`, `POSTGRES_PASSWORD`, `IMPORT_TOKEN`.
- [ ] Принято решение по временному HTTPS: self-signed сертификат.

### 1.4 Данные и watcher
- [ ] Подтвержден источник файлов для watcher (локальная папка или SMB).
- [ ] Подготовлены права доступа к `data/watch`, `data/processed`, `data/quarantine`.
- [ ] Определены smoke-файлы для тестового импорта (JSON/CSV).

### 1.5 Эксплуатация
- [ ] Определены политика backup/restore и окно восстановления.
- [ ] Подготовлен rollback-план (версия, образы, команда отката).
- [ ] Согласован приемочный чек-лист после cutover в ЛВС.

## 2. Развертывание на VM с интернетом

### 2.1 Подготовка окружения
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/generate_env.sh --production
```

При использовании Docker:
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod build
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py migrate
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py createsuperuser
```

### 2.2 Базовые проверки
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.proxy.yml up -d
curl http://localhost/health
docker compose -f docker-compose.prod.yml --env-file .env.prod logs web --tail=100
docker compose -f docker-compose.prod.yml --env-file .env.prod logs watcher --tail=100
```

Проверить в UI:
- [ ] логин администратором;
- [ ] дашборд;
- [ ] статистика;
- [ ] дерево событий.

### 2.3 Проверка watcher
- [ ] Положить тестовый JSON/CSV в watch-каталог.
- [ ] Убедиться, что файлы обработаны и перемещены в `processed`/`quarantine`.
- [ ] Проверить, что данные появились в приложении.

## 3. HTTPS (временный self-signed)

Рекомендуемый минимум:
- создать временный локальный Root CA;
- выпустить server cert с SAN (FQDN и, при необходимости, IP);
- подключить cert/key в Nginx и включить редирект `80 -> 443`.

Проверка:
```bash
curl -vk https://<FQDN_OR_IP>/health/
```

Приемка HTTPS:
- [ ] TLS поднимается стабильно после перезапуска контейнеров.
- [ ] На целевых клиентах сертификат доверен (через импорт root CA).

## 4. Подготовка к офлайн-режиму (до отключения интернета)

### 4.1 Зафиксировать релиз
- [ ] Зафиксирован commit/tag релиза.
- [ ] Сохранены конфиги (`docker-compose*.yml`, nginx, `.env.prod`) в защищенном месте.

### 4.2 Подготовить Docker-образы
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod build
docker save $(docker compose -f docker-compose.prod.yml --env-file .env.prod config --images) -o advisor-dj-images.tar
```

- [ ] Архив образов сохранен на VM и во внешнем безопасном хранилище.

### 4.3 Резервное копирование
- [ ] Выполнен backup БД.
- [ ] Выполнен тестовый restore в отдельном окружении/контейнере.

## 5. Переключение VM в внутреннюю ЛВС

### 5.1 Сетевой cutover
- [ ] VM переведена в целевой сегмент ЛВС.
- [ ] Обновлены DNS/hosts для внутреннего адреса.
- [ ] Проверены сетевые доступы от клиентских рабочих мест.

### 5.2 Проверка после переключения
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl -k https://<FQDN_OR_IP>/health/
docker compose -f docker-compose.prod.yml --env-file .env.prod logs --tail=100
```

- [ ] `web`, `db`, `watcher` в состоянии `healthy`.
- [ ] UI доступен по HTTPS из ЛВС.
- [ ] Импорт через watcher проходит end-to-end.

## 6. Go/No-Go критерии

Go, если:
- [ ] `DEBUG=0`, корректный `ALLOWED_HOSTS`.
- [ ] HTTPS работает и принимается клиентами.
- [ ] Базовая функциональность подтверждена (dashboard/statistics/tree/import).
- [ ] backup и restore проверены.
- [ ] Есть рабочий rollback-план.

No-Go, если:
- [ ] недоступен `/health/`;
- [ ] watcher не обрабатывает файлы;
- [ ] TLS нестабилен или недоверен на ключевых клиентах;
- [ ] нет подтвержденного восстановления из backup.

## 7. Rollback (кратко)

1. Остановить текущий стек: `docker compose -f docker-compose.prod.yml --env-file .env.prod down`.
2. Загрузить предыдущие образы (если нужно): `docker load -i <backup-images.tar>`.
3. Вернуть предыдущие `docker-compose`/nginx/.env.prod.
4. Поднять стек: `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d`.
5. При необходимости восстановить БД из последнего валидного backup.

## 8. Следующий этап (после восстановления MS CA)

- Выпустить внутренний сертификат от MS CA на тот же `FQDN`.
- Заменить временный self-signed cert в Nginx.
- Перезапустить Nginx и повторить TLS-проверки.
- Вывести временный root CA из доверенных хранилищ по плану.
