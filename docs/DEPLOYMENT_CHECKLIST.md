---
title: "Чеклист развертывания для ЛВС без интернета"
type: deployment
status: draft
date: 2025-01-30
last_verified: "2026-02-20"
verified_against_commit: "latest"
owner: "@rom"
---

[← Deployment Readiness](DEPLOYMENT_READINESS.md) · [Back to README](../README.md) · [Deploy Plan →](DEPLOY_PLAN.md)

# Чеклист развертывания Print Advisor в ЛВС без интернета

## ✅ Что уже работает

### 1. Docker-композиция
- ✅ `docker-compose.yml` настроен с тремя сервисами: `web`, `watcher`, `db`
- ✅ PostgreSQL контейнер настроен и работает
- ✅ Все сервисы связаны через внутреннюю сеть `advisor-network`
- ✅ Health checks настроены для всех сервисов

### 2. PostgreSQL
- ✅ Используется официальный образ `postgres:15`
- ✅ Настройка через переменные окружения (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`)
- ✅ Данные сохраняются в volume `pgdata`
- ✅ Django настроен на использование PostgreSQL через `DATABASE_URL`

### 3. Watcher (демон мониторинга каталога)
- ✅ Сервис `watcher` следит за каталогом `/app/data/watch`
- ✅ Автоматически обрабатывает:
  - **JSON-файлы** → импорт событий печати
  - **CSV-файлы** → импорт пользователей
- ✅ Перемещает обработанные файлы в `/app/data/processed`
- ✅ Перемещает файлы с ошибками в `/app/data/quarantine`
- ✅ Логирование всех действий

### 4. Импорт данных
- ✅ Импорт событий печати из JSON (`printing/services.py::import_print_events`)
- ✅ Импорт пользователей из CSV (`printing/services.py::import_users_from_csv_stream`)
- ✅ Автоматическое создание отсутствующих пользователей
- ✅ Дедупликация по `job_id` для событий печати

---

## ⚠️ Что нужно настроить для работы с Windows-сервером

Рекомендуемый путь для production: транзитные каталоги (`inbox`) + локальный ingest (`scripts/ingest_mover.sh` + systemd timer).
См. `docs/how-to/transit-ingest-pipeline.md`.

### 1. Монтирование сетевой папки в Docker

**Проблема:** Текущий `docker-compose.yml` использует Docker volume `data`, который создается локально. Для работы с файлами с Windows-сервера нужно примонтировать сетевую папку.

**Решение:** Добавить bind mount для каталога watch.

**Вариант А: Монтирование сетевой папки на хост-систему, затем в контейнер**

1. На Linux хосте смонтировать Windows-шару (SMB/CIFS):
```bash
# Установить cifs-utils (если нет)
sudo apt-get install cifs-utils

# Создать точку монтирования
sudo mkdir -p /mnt/printshare

# Смонтировать Windows-шару
sudo mount -t cifs //windows-server/share /mnt/printshare \
  -o username=user,password=pass,uid=$(id -u),gid=$(id -g),iocharset=utf8

# Или добавить в /etc/fstab для автозапуска:
//windows-server/share /mnt/printshare cifs username=user,password=pass,uid=1000,gid=1000,iocharset=utf8 0 0
```

2. Обновить `docker-compose.yml`:
```yaml
watcher:
  volumes:
    - logs:/app/logs
    - /mnt/printshare:/app/data/watch:ro  # Только чтение для безопасности
    - ./data/processed:/app/data/processed
    - ./data/quarantine:/app/data/quarantine
```

**Вариант Б: Прямое монтирование через Docker volume driver (требует плагин)**

Можно использовать плагин для CIFS, но вариант А проще и надежнее.

### 2. Права доступа к файлам

**Проблема:** Файлы, скопированные с Windows-сервера, могут иметь другие права доступа.

**Решение:** 
- Использовать опцию `uid` и `gid` при монтировании CIFS
- Или настроить `user` в docker-compose.yml для соответствия UID/GID

### 3. Работа без интернета

**Важно:** Docker-образы нужно собрать **один раз** на машине с интернетом, затем скопировать на целевую машину.

**Процесс:**

1. **На машине с интернетом:**
```bash
# Собрать production-образы
docker compose -f docker-compose.prod.yml --env-file .env.prod build

# Сохранить образы в архив
docker save \
  advisor-dj-web:latest \
  advisor-dj-watcher:latest \
  postgres:15 \
  -o advisor-dj-images.tar

# Скопировать на целевую машину (через USB/локальную сеть)
scp advisor-dj-images.tar user@target-server:/tmp/
```

2. **На целевой машине (без интернета):**
```bash
# Загрузить образы
docker load -i /tmp/advisor-dj-images.tar

# Запустить production композицию
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

**Альтернатива:** Использовать Docker Registry в локальной сети (если есть).

### 4. Настройка переменных окружения

**Рекомендуемый способ:** Использовать скрипт автоматической генерации:

```bash
# Автоматическая генерация .env.prod со всеми ключами
./scripts/generate_env.sh --production

# Или интерактивный режим для настройки параметров
./scripts/generate_env.sh --production --interactive

# С указанием IP адресов сервера
./scripts/generate_env.sh --allowed-hosts "192.168.1.100,localhost,127.0.0.1"
```

Скрипт автоматически генерирует:
- `SECRET_KEY` (безопасный ключ Django)
- `POSTGRES_PASSWORD` (64 символа)
- `IMPORT_TOKEN` (токен для импорта)
- Определяет `ALLOWED_HOSTS` (автоматически или вручную)

**Ручной способ (если скрипт недоступен):**

Создать `.env.prod` файл вручную:

```bash
# База данных
POSTGRES_DB=advisor
POSTGRES_USER=advisor
POSTGRES_PASSWORD=your-strong-password-here  # Генерировать: openssl rand -base64 48
POSTGRES_PORT=5432

# Django
DEBUG=0
SECRET_KEY=your-very-long-secret-key-here-min-50-chars  # Генерировать через Django
ALLOWED_HOSTS=your-server-ip,localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.production

# Логи
LOG_TO_FILE=1
LOG_TO_CONSOLE=0
LOG_DIR=/app/logs
LOG_FILE_NAME=project.log
WATCHER_LOG_FILE_NAME=print_events_watcher.log

# Watcher
PRINT_EVENTS_WATCH_DIR=/app/data/watch
PRINT_EVENTS_PROCESSED_DIR=/app/data/processed
PRINT_EVENTS_QUARANTINE_DIR=/app/data/quarantine
IMPORT_TOKEN=your-import-token  # Генерировать: openssl rand -hex 32
ENABLE_WINDOWS_AUTH=0

# Порты
# Применяется только если включён проброс порта web в docker-compose.yml
WEB_PORT=8000
```

---

## 📋 Пошаговая инструкция развертывания

### Этап 1: Подготовка на машине с интернетом

```bash
# 1. Клонировать проект
git clone <repository-url>
cd advisor-dj

# 2. Собрать production-образы
docker compose -f docker-compose.prod.yml --env-file .env.prod build

# 3. Создать архив образов
docker save \
  $(docker compose -f docker-compose.prod.yml --env-file .env.prod config --images) \
  -o advisor-dj-images.tar

# 4. Скопировать файлы проекта и архив на целевую машину
scp -r . user@target-server:/opt/advisor-dj/
scp advisor-dj-images.tar user@target-server:/opt/advisor-dj/
```

### Этап 2: Настройка на целевой машине (без интернета)

```bash
# 1. Загрузить образы
cd /opt/advisor-dj
docker load -i advisor-dj-images.tar

# 2. Смонтировать Windows-шару (если еще не смонтирована)
sudo mkdir -p /mnt/printshare
sudo mount -t cifs //windows-server/printshare /mnt/printshare \
  -o username=service_account,password=password,uid=1000,gid=1000,iocharset=utf8

# 3. Обновить docker-compose.yml для использования сетевой папки
# (см. раздел "Монтирование сетевой папки" выше)

# 4. Создать .env.prod файл с настройками
cp .env.prod.template .env.prod
nano .env.prod  # Отредактировать значения

# 5. Создать директории для processed и quarantine
mkdir -p ./data/processed ./data/quarantine
chmod 755 ./data/processed ./data/quarantine

# 6. Запустить сервисы
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 7. Выполнить миграции БД
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py migrate

# 6. Настроить автозапуск при старте системы (опционально)
sudo cp advisor-dj.service /etc/systemd/system/
# Если проект размещен не в /opt/advisor-dj, обновить WorkingDirectory
sudo sed -i 's|^WorkingDirectory=.*|WorkingDirectory=/path/to/advisor-dj|' /etc/systemd/system/advisor-dj.service
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service

# 7. Создать суперпользователя (опционально)
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py createsuperuser

# 8. Проверить статус
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f watcher  # Просмотр логов watcher
```

### Этап 3: Проверка работы

1. **Проверить, что сервисы запущены:**
```bash
docker compose ps
# Все сервисы должны быть в статусе "Up (healthy)"
```

2. **Проверить логи watcher:**
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs watcher | tail -20
# Должно быть: "Слежение за /app/data/watch..."
```

3. **Проверить доступность веб-интерфейса:**
```bash
curl http://localhost/health
# Должен вернуть {"status": "healthy", ...}
```

4. **Тестовый импорт:**
   - Скопировать тестовый JSON-файл с событиями в `/mnt/printshare/` (или в смонтированную папку)
   - Проверить, что файл обработан:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.prod logs watcher | grep "Загружено"
   ls -la ./data/processed/  # Файл должен быть перемещен сюда
   ```

---

## 🔧 Рекомендуемые изменения docker-compose.yml

Для работы с Windows-шарой обновить секцию `watcher`:

```yaml
watcher:
  build:
    context: .
    dockerfile: Dockerfile.watcher
  container_name: advisor-watcher
  environment:
    - DEBUG=${DEBUG:-0}
    - DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.production}
    - SECRET_KEY=${SECRET_KEY}
    - DATABASE_URL=postgres://${POSTGRES_USER:-advisor}:${POSTGRES_PASSWORD:-advisor}@db:5432/${POSTGRES_DB:-advisor}
    - LOG_TO_FILE=${LOG_TO_FILE:-1}
    - LOG_TO_CONSOLE=${LOG_TO_CONSOLE:-0}
    - LOG_DIR=${LOG_DIR:-/app/logs}
    - WATCHER_LOG_FILE_NAME=${WATCHER_LOG_FILE_NAME:-print_events_watcher.log}
    - PRINT_EVENTS_WATCH_DIR=${PRINT_EVENTS_WATCH_DIR:-/app/data/watch}
    - PRINT_EVENTS_PROCESSED_DIR=${PRINT_EVENTS_PROCESSED_DIR:-/app/data/processed}
    - PRINT_EVENTS_QUARANTINE_DIR=${PRINT_EVENTS_QUARANTINE_DIR:-/app/data/quarantine}
  volumes:
    - logs:/app/logs
    # Монтирование сетевой папки с Windows-сервера (только чтение)
    - /mnt/printshare:/app/data/watch:ro
    # Локальные директории для processed и quarantine
    - ./data/processed:/app/data/processed
    - ./data/quarantine:/app/data/quarantine
  depends_on:
    web:
      condition: service_healthy
    db:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "pgrep", "-f", "printing.print_events_watcher"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  networks:
    - advisor-network
  restart: unless-stopped  # Автоматический перезапуск всех контейнеров
```

**Примечание:** Все сервисы (`db`, `web`, `watcher`) имеют политику `restart: unless-stopped` для автоматического перезапуска. Для автозапуска при перезагрузке системы используйте systemd unit файл `advisor-dj.service`.

---

## ⚠️ Потенциальные проблемы и решения

### Проблема 1: Файлы не обрабатываются

**Причины:**
- Неправильные права доступа на файлы
- Watcher не видит файлы из-за задержки копирования
- Файлы заблокированы Windows-сервером

**Решение:**
- Использовать `:ro` (read-only) для watch директории
- Убедиться, что файлы полностью скопированы (watcher реагирует на событие `on_created`)
- Настроить retry логику (уже есть в коде)

### Проблема 2: Потеря соединения с сетевой папкой

**Решение:**
- Настроить автопереподключение в `/etc/fstab` с опциями `_netdev` и `auto`
- Добавить мониторинг доступности папки
- Использовать `restart: unless-stopped` для контейнера (уже есть)

### Проблема 3: Кодировка файлов

**Решение:**
- Код уже использует `utf-8-sig` для CSV и JSON
- Убедиться, что файлы с Windows-сервера сохраняются в UTF-8

### Проблема 4: Производительность на больших файлах

**Решение:**
- Текущий код уже оптимизирован (батчинг по 100 событий)
- Для очень больших файлов можно увеличить `BATCH_SIZE` в `services.py`

---

## ✅ Итоговый ответ

**Да, ваше приложение БУДЕТ выполнять нужные функции, но с небольшими настройками:**

1. ✅ **Docker в ЛВС** - работает, образы нужно собрать один раз с интернетом
2. ✅ **PostgreSQL** - полностью настроен
3. ✅ **Загрузка из каталога** - работает, нужно только примонтировать Windows-шару
4. ✅ **Автоматическая обработка** - watcher следит за каталогом и обрабатывает файлы

**Что нужно сделать:**
- Смонтировать Windows-шару на Linux хосте
- Обновить `docker-compose.yml` для использования bind mount вместо volume
- Собрать образы на машине с интернетом и скопировать на целевую
- Настроить `.env.prod` файл

**Все остальное уже работает!** 🎉

## See Also

- [Getting Started](getting-started.md) - базовый путь запуска
- [Deployment](deployment.md) - актуальный сценарий деплоя
- [Troubleshooting](troubleshooting.md) - диагностика типовых проблем
