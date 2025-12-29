# Установка Print Advisor в Docker

## Быстрая установка

### Шаг 1: Настройка прав доступа к Docker

Если получаете ошибку `permission denied` при работе с Docker, выполните:

```bash
# Добавить пользователя в группу docker (требует перелогина)
sudo usermod -aG docker $USER
# Затем выйдите и войдите снова, или выполните:
newgrp docker
```

Или используйте `sudo` для всех команд Docker (менее безопасно).

### Шаг 2: Генерация .env файла

```bash
# Автоматическая генерация
./scripts/generate_env.sh

# Или интерактивный режим
./scripts/generate_env.sh --interactive

# Или с указанием хостов
./scripts/generate_env.sh --allowed-hosts "192.168.1.100,localhost,127.0.0.1"
```

### Шаг 3: Создание сети для Nginx (один раз)

```bash
# С sudo (если нет прав)
sudo docker network create reverse-proxy-network

# Или без sudo (если в группе docker)
docker network create reverse-proxy-network
```

### Шаг 4: Сборка образов

```bash
# С sudo
sudo docker compose build

# Или без sudo
docker compose build
```

### Шаг 5: Запуск контейнеров

```bash
# С sudo
sudo docker compose up -d

# Или без sudo
docker compose up -d

# Или с пересборкой
sudo docker compose up --build -d
```

### Шаг 6: Выполнение миграций

```bash
# С sudo
sudo docker compose exec web python manage.py migrate

# Или без sudo
docker compose exec web python manage.py migrate
```

### Шаг 7: Сборка статических файлов

```bash
# С sudo
sudo docker compose exec web python manage.py collectstatic --noinput

# Или без sudo
docker compose exec web python manage.py collectstatic --noinput
```

### Шаг 8: Создание суперпользователя (опционально)

```bash
# С sudo
sudo docker compose exec web python manage.py createsuperuser

# Или без sudo
docker compose exec web python manage.py createsuperuser
```

### Шаг 9: Проверка работоспособности

```bash
# Проверка статуса контейнеров
sudo docker compose ps

# Проверка health check
curl http://localhost:8001/health/

# Или запуск smoke тестов
sudo ./scripts/smoke.sh
```

## Использование Makefile (если есть права)

Если вы в группе `docker`, можно использовать Makefile:

```bash
# Сборка и запуск
make up-build

# Миграции
make migrate

# Статика
make collectstatic

# Проверка
make smoke

# Статус
make status
```

## Проверка установки

После установки проверьте:

1. **Статус контейнеров:**
   ```bash
   sudo docker compose ps
   ```
   Все контейнеры должны быть в статусе `Up (healthy)`

2. **Health check:**
   ```bash
   curl http://localhost:8001/health/
   ```
   Должен вернуть JSON с `"status": "healthy"`

3. **Логи:**
   ```bash
   sudo docker compose logs web --tail=50
   sudo docker compose logs watcher --tail=50
   ```

4. **Доступ к веб-интерфейсу:**
   Откройте в браузере: `http://localhost:8001` (или IP адрес из ALLOWED_HOSTS)

## Решение проблем

### Ошибка "permission denied"

**Решение 1:** Добавить пользователя в группу docker:
```bash
sudo usermod -aG docker $USER
newgrp docker  # или перелогиниться
```

**Решение 2:** Использовать sudo для всех команд Docker

### Ошибка "network not found"

Создайте сеть вручную:
```bash
sudo docker network create reverse-proxy-network
```

### Ошибка "port already in use"

Измените порт в `.env`:
```env
WEB_PORT=8002  # вместо 8001
```

### База данных не запускается

Проверьте логи:
```bash
sudo docker compose logs db
```

Убедитесь, что каталог `pgdata` не занят другим контейнером.

## Следующие шаги

После успешной установки:

1. Настроить Nginx reverse proxy (см. `docs/NGINX_SETUP.md`)
2. Настроить автозапуск (см. `advisor-dj.service`)
3. Настроить бэкапы БД
4. Настроить мониторинг

