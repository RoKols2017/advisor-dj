# 🚀 Быстрое развертывание Print Advisor с Nginx

## Выполните эти команды в терминале:

```bash
cd /home/oitroot/project/advisor-dj

# 1. Создать сеть для reverse proxy (один раз)
docker network create reverse-proxy-network

# 2. Запустить Nginx reverse proxy
docker compose -f docker-compose.proxy.yml up -d

# 3. Сгенерировать production env
./scripts/generate_env.sh --production

# 4. Собрать и запустить основное приложение (production)
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 5. Подождать 30 секунд для запуска сервисов
sleep 30

# 6. Выполнить миграции БД
docker compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# 7. Создать суперпользователя (интерактивно)
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 8. Проверить статус
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.proxy.yml ps

# 9. Проверить health checks
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
- **Логи приложения:** `docker compose -f docker-compose.prod.yml logs -f web`
- **Логи watcher:** `docker compose -f docker-compose.prod.yml logs -f watcher`

## Если возникнут проблемы:

1. Проверьте права на каталоги: `ls -la data/`
2. Проверьте логи: `docker compose -f docker-compose.prod.yml logs`
3. Проверьте статус: `docker compose -f docker-compose.prod.yml ps`
