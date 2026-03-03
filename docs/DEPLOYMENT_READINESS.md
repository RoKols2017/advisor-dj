---
title: "Готовность к развертыванию на новом сервере"
type: guide
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

[← Status](STATUS.md) · [Back to README](../README.md) · [Deployment Checklist →](DEPLOYMENT_CHECKLIST.md)

# Готовность к развертыванию на новом сервере

**Дата проверки:** 2025-12-23  
**Статус:** ✅ **ГОТОВО К РАЗВЕРТЫВАНИЮ**

## ✅ Что готово

### 1. Конфигурация Docker

- ✅ `docker-compose.yml` - настроен для всех сервисов (web, watcher, db)
- ✅ `docker-compose.proxy.yml` - Nginx reverse proxy (отдельный файл)
- ✅ `restart: unless-stopped` - настроен для всех сервисов (автоматический перезапуск)
- ✅ `Dockerfile` - для web-контейнера
- ✅ `Dockerfile.watcher` - для watcher-контейнера
- ✅ Структура каталогов `data/` (watch, processed, quarantine)
- ✅ `infrastructure/nginx/` - конфигурации Nginx
- ✅ `advisor-dj.service` - шаблон systemd unit файла для автозапуска (перед применением обновите `User/Group/WorkingDirectory` под целевой сервер)

### 1.1. Nginx Reverse Proxy

- ✅ Nginx работает в отдельном контейнере (порт 80/443)
- ✅ Единая точка входа для всех сервисов
- ✅ Модульная структура конфигов (conf.d, snippets)
- ✅ Поддержка SSL/TLS с сертификатами MS CA (для этапа B)
- ✅ Заложена поддержка для будущего n8n

### 2. Переменные окружения

- ✅ `.env` файл создан с необходимыми переменными:
  - `SECRET_KEY` - сгенерирован безопасный ключ
  - `POSTGRES_PASSWORD` - сгенерирован безопасный пароль
  - `ALLOWED_HOSTS` - настроен (нужно обновить на новом сервере)
  - Все остальные необходимые переменные присутствуют

### 3. Функциональность

- ✅ Все критические ошибки исправлены
- ✅ Watcher обрабатывает существующие и новые файлы
- ✅ Права доступа настроены и задокументированы
- ✅ Дерево событий работает корректно
- ✅ Автоматическая загрузка файлов работает

### 4. Документация

- ✅ `docs/DEPLOYMENT_CHECKLIST.md` - чеклист развертывания
- ✅ `docs/FILE_WATCHER_SETUP.md` - настройка watcher и прав доступа
- ✅ `docs/NGINX_REVERSE_PROXY_ARCHITECTURE.md` - архитектура Nginx reverse proxy
- ✅ `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md` - пошаговый план внедрения Nginx
- ✅ `infrastructure/README.md` - краткая инструкция по инфраструктуре
- ✅ `README.md` - общая информация о проекте

## ⚠️ Что нужно сделать на новом сервере

### 1. Обновить `.env` файл

**Критично:** Обновить следующие переменные для нового сервера:

```env
# Обновить ALLOWED_HOSTS с IP/доменом нового сервера
ALLOWED_HOSTS=<IP_НОВОГО_СЕРВЕРА>,localhost,127.0.0.1

# Опционально: сгенерировать новые SECRET_KEY и POSTGRES_PASSWORD
# (или оставить существующие, если они безопасны)
```

**Генерация новых ключей:**
```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# POSTGRES_PASSWORD (64 символа)
openssl rand -base64 48
```

### 1.1. Настройка Nginx Reverse Proxy

**Для этапа разработки (HTTP-only):**
```bash
# Создать сеть (один раз)
docker network create reverse-proxy-network

# Запустить Nginx
docker compose -f docker-compose.proxy.yml up -d
```

**Для production (HTTPS с MS CA сертификатами):**
См. подробную инструкцию в `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md` (Этап B).

### 2. Права доступа к каталогам

Выполнить на новом сервере после копирования проекта:

```bash
# Создать каталоги (если их нет)
mkdir -p data/{watch,processed,quarantine}

# Установить права доступа
sudo chmod 777 data/{watch,processed,quarantine}
```

Или альтернативный вариант (более безопасный):
```bash
sudo chown -R 999:999 data/{watch,processed,quarantine}
sudo chmod 775 data/{watch,processed,quarantine}
```

### 3. Подготовка к работе без интернета

**Важно:** Если новый сервер без интернета, нужно:

#### Вариант A: Собрать образы заранее

На машине с интернетом:
```bash
# Собрать образы
docker compose build

# Сохранить образы в архив
docker save \
  advisor-dj-web:latest \
  advisor-dj-watcher:latest \
  postgres:15 \
  -o advisor-dj-images.tar

# Скопировать архив на новый сервер (USB/локальная сеть)
```

На новом сервере (без интернета):
```bash
# Загрузить образы
docker load -i advisor-dj-images.tar

# Запустить
docker compose up -d
```

#### Вариант B: Использовать локальный Docker Registry

Если есть локальный Docker Registry в сети, можно использовать его.

### 4. Монтирование Windows-шары (опционально)

Если нужно монтировать Windows-шару вместо локального каталога:

1. Установить `cifs-utils`:
   ```bash
   sudo apt-get update && sudo apt-get install -y cifs-utils
   ```

2. Создать файл с учетными данными:
   ```bash
   echo "username=your_user
   password=your_password" > /etc/samba/credentials
   chmod 600 /etc/samba/credentials
   ```

3. Добавить в `/etc/fstab`:
   ```
   //windows-server/share /path/to/data cifs credentials=/etc/samba/credentials,uid=1000,gid=1000,iocharset=utf8,file_mode=0777,dir_mode=0777 0 0
   ```

4. Обновить `docker-compose.yml` для использования монтированного каталога вместо `./data`

## 📋 Пошаговая инструкция развертывания

### Шаг 1: Копирование проекта

```bash
# На новом сервере
cd /opt  # или другой каталог
git clone <repository-url> advisor-dj
cd advisor-dj
```

Или скопировать проект через scp/rsync:
```bash
scp -r advisor-dj user@new-server:/opt/
```

### Шаг 2: Настройка переменных окружения

**Рекомендуемый способ:** Использовать скрипт генерации .env файла:

```bash
cd /opt/advisor-dj

# Автоматическая генерация со всеми необходимыми ключами
./scripts/generate_env.sh

# Или интерактивный режим (для настройки параметров)
./scripts/generate_env.sh --interactive

# Или с указанием разрешенных хостов
./scripts/generate_env.sh --allowed-hosts "192.168.1.100,localhost,127.0.0.1"
```

**Альтернативный способ (ручной):**

```bash
cd /opt/advisor-dj
cp .env.example .env  # если есть шаблон

# Отредактировать .env
nano .env

# Обязательно обновить:
# - ALLOWED_HOSTS=<IP_СЕРВЕРА>
# - SECRET_KEY (сгенерировать: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
# - POSTGRES_PASSWORD (сгенерировать: openssl rand -base64 48)
```

### Шаг 3: Настройка каталогов и прав

```bash
# Создать каталоги
mkdir -p data/{watch,processed,quarantine}

# Установить права
sudo chmod 777 data/{watch,processed,quarantine}
```

### Шаг 4: Загрузка Docker-образов (если без интернета)

```bash
# Если образы были сохранены заранее
docker load -i advisor-dj-images.tar
```

### Шаг 5: Сборка и запуск

```bash
# Если есть интернет - собрать образы
docker compose build

# Или если образы уже загружены - просто запустить
docker compose up -d
```

### Шаг 6: Выполнение миграций

```bash
docker compose exec web python manage.py migrate
```

### Шаг 7: Создание суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

### Шаг 8: Настройка автозапуска при старте системы (опционально)

Для автоматического запуска контейнеров при перезагрузке сервера:

```bash
# Скопировать systemd unit файл
sudo cp advisor-dj.service /etc/systemd/system/

# Если проект размещен не в /opt/advisor-dj, обновить WorkingDirectory
sudo sed -i 's|^WorkingDirectory=.*|WorkingDirectory=/path/to/advisor-dj|' /etc/systemd/system/advisor-dj.service

# Перезагрузить конфигурацию systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable advisor-dj.service

# Запустить сервис
sudo systemctl start advisor-dj.service

# Проверить статус
sudo systemctl status advisor-dj.service
```

**Примечание:** Все контейнеры уже имеют политику `restart: unless-stopped`, которая обеспечивает автоматический перезапуск при перезапуске Docker. Systemd сервис нужен для запуска контейнеров после полной перезагрузки системы.

### Шаг 9: Проверка работоспособности

```bash
# Проверить статус
docker compose ps

# Проверить health check
curl http://localhost/health

# Проверить логи
docker compose logs web
docker compose logs watcher
```

## 🔍 Проверка после развертывания

### Базовая проверка

1. ✅ Все контейнеры в статусе `healthy`
2. ✅ Health check возвращает 200: `curl http://localhost/health`
3. ✅ Веб-интерфейс доступен: `http://<SERVER_IP>/`
4. ✅ Watcher обрабатывает файлы из `data/watch/`

### Проверка функциональности

1. ✅ Вход в систему через созданного суперпользователя
2. ✅ Отображение дашборда
3. ✅ Отображение дерева событий (`/tree/`)
4. ✅ Отображение статистики (`/statistics/`)
5. ✅ Загрузка файлов в `data/watch/` и их автоматическая обработка

## 📝 Примечания

### Критические моменты

1. **ALLOWED_HOSTS** - обязательно обновить на новом сервере, иначе Django будет отклонять запросы
2. **Права доступа** - без правильных прав watcher не сможет перемещать файлы
3. **Без интернета** - образы нужно загрузить заранее
4. **Миграции** - обязательно выполнить `migrate` при первом запуске

### Рекомендации

- Создать резервные копии `.env` файла (хранить безопасно)
- Настроить автоматическое резервное копирование БД
- Настроить ротацию логов
- Рассмотреть использование Docker secrets для паролей в production

## 📚 Дополнительная документация

- `docs/DEPLOYMENT_CHECKLIST.md` - подробный чеклист развертывания
- `docs/FILE_WATCHER_SETUP.md` - настройка watcher и прав доступа
- `docs/DEPLOY_GUIDE.md` - общее руководство по развертыванию
- `README.md` - общая информация о проекте

## ✅ Итог

Приложение **готово к развертыванию** на новом сервере. Все необходимые компоненты на месте, документация создана, функциональность проверена и работает.

**Минимальные действия на новом сервере:**
1. Обновить `ALLOWED_HOSTS` в `.env`
2. Настроить права доступа к каталогам `data/`
3. Загрузить Docker-образы (если без интернета)
4. Запустить `docker compose up -d`
5. Выполнить миграции и создать суперпользователя

После этого приложение будет готово к работе.

## See Also

- [Getting Started](getting-started.md) - базовый путь запуска
- [Deployment](deployment.md) - актуальный сценарий деплоя
- [Troubleshooting](troubleshooting.md) - диагностика типовых проблем
