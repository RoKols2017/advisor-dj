---
title: "Статус выполнения pre-flight (VM -> ЛВС)"
type: guide
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

# Статус выполнения pre-flight (VM -> ЛВС)

Документ фиксирует фактический прогресс по `docs/how-to/vm-lan-deployment-preflight.md`.

## Выполнено сейчас

- [x] Проверен git-контекст: репозиторий доступен, активная ветка `master`.
- [x] Проверена доступность Docker CLI: `Docker 29.2.1`.
- [x] Проверена доступность Docker Compose CLI: `v5.0.2`.
- [x] Проверено свободное место на диске `/`: ~`430G` свободно.
- [x] Проверена исходящая сеть: HTTPS-доступ в интернет есть (`https://pypi.org` отвечает).
- [x] Валидирован `docker compose config` (конфиг читается).
- [x] Созданы рабочие каталоги данных:
  - `data/watch`
  - `data/processed`
  - `data/quarantine`

## Выявленные блокеры

- [ ] Нет доступа к Docker daemon для текущего пользователя:
  - ошибка: `permission denied while trying to connect to /var/run/docker.sock`
- [ ] В системе отсутствует `make` (`make: команда не найдена`).
- [ ] В системе нет Python 3.13:
  - есть `python3 3.12.3`
  - `python3.13` не найден.
- [ ] `.env.prod` не создан, поэтому при `docker compose config` есть предупреждения:
  - `SECRET_KEY variable is not set`
  - `IMPORT_TOKEN variable is not set`

## Что нужно сделать дальше (следующий шаг)

1. Дать пользователю `roman` доступ к Docker daemon (группа `docker` + перелогин).
2. Установить `make` (пакет `make`/`build-essential` для Ubuntu).
3. Установить Python 3.13 (или подтвердить, что запуск будет только через Docker-образы).
4. Сформировать `.env.prod` через `scripts/generate_env.sh --production` и заполнить секреты.

## Точка возобновления после перезагрузки

Текущий статус: pre-flight остановлен на шаге получения доступа к Docker daemon.

Порядок действий после перезагрузки:

1. Проверить, что пользователь получил доступ к Docker:

```bash
docker info --format '{{.ServerVersion}}'
```

2. Если доступ есть, сразу перейти к запуску стека и проверкам:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py migrate
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl http://localhost/health
docker compose -f docker-compose.prod.yml --env-file .env.prod logs web --tail=100
docker compose -f docker-compose.prod.yml --env-file .env.prod logs watcher --tail=100
```

3. Если доступа нет, повторить шаг с группой Docker и снова перелогиниться:

```bash
sudo usermod -aG docker $USER
newgrp docker
docker info --format '{{.ServerVersion}}'
```

4. После подтверждения доступа продолжить pre-flight по файлу
`docs/how-to/vm-lan-deployment-preflight.md` (раздел 2).

## Команды, которыми продолжим после снятия блокеров

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py migrate
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
curl http://localhost/health
docker compose -f docker-compose.prod.yml --env-file .env.prod logs web --tail=100
docker compose -f docker-compose.prod.yml --env-file .env.prod logs watcher --tail=100
```
