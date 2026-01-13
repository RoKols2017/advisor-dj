# 🚀 Быстрое развертывание Print Advisor с Nginx

## Выполните эти команды в терминале:

```bash
cd /home/oitroot/project/advisor-dj

# 1. Создать сеть для reverse proxy (один раз)
docker network create reverse-proxy-network

# 2. Запустить Nginx reverse proxy
docker compose -f docker-compose.proxy.yml up -d

# 3. Собрать и запустить основное приложение
docker compose build
docker compose up -d

# 4. Подождать 30 секунд для запуска сервисов
sleep 30

# 5. Выполнить миграции БД
docker compose exec web python manage.py migrate --noinput

# 6. Создать суперпользователя (интерактивно)
docker compose exec web python manage.py createsuperuser

# 7. Проверить статус
docker compose ps
docker compose -f docker-compose.proxy.yml ps

# 8. Проверить health checks
curl http://localhost/health
curl http://localhost/health/
```

## Или используйте готовый скрипт:

```bash
cd /home/oitroot/project/advisor-dj
./scripts/deploy_all.sh
```

## После развертывания:

- **Приложение доступно:** http://localhost/
- **Логи Nginx:** `docker compose -f docker-compose.proxy.yml logs -f nginx`
- **Логи приложения:** `docker compose logs -f web`
- **Логи watcher:** `docker compose logs -f watcher`

## Если возникнут проблемы:

1. Проверьте права на каталоги: `ls -la data/`
2. Проверьте логи: `docker compose logs`
3. Проверьте статус: `docker compose ps`
