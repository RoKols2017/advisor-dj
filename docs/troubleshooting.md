[← Security](security.md) · [Back to README](../README.md)

# Troubleshooting

## Docker: permission denied

Симптом: пользователь добавлен в группу `docker`, но команды не работают в текущей сессии.

Быстрые варианты:

```bash
newgrp docker
docker ps
```

```bash
sg docker -c "docker ps"
```

Если не помогло, перелогиньтесь:

```bash
su - $USER
```

## Nginx не поднимается или приложение недоступно

Проверьте по шагам:

```bash
docker network create reverse-proxy-network 2>/dev/null || true
docker compose ps
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.proxy.yml ps
curl http://localhost/health
```

Если `advisor-web` не в нужной сети, перезапустите основной стек:

```bash
docker compose down
docker compose up -d
```

## Watcher не двигает файлы

Проверьте права и логи:

```bash
ls -ld data/watch data/processed data/quarantine
docker compose ps watcher
docker compose logs watcher --tail=100
docker compose exec watcher ls -la /app/data/watch/
```

## Частые причины с TLS/HTTPS

- ключ и сертификат не соответствуют
- не включен порт `443:443` в `docker-compose.proxy.yml`
- не обновлен `CSRF_TRUSTED_ORIGINS`

## Что объединено в этот документ

Содержимое из прежних root-файлов:
- `FIX_DOCKER_ACCESS.md`
- `QUICK_START_NGINX.md`

Оригиналы оставлены в корне до финальной очистки.

## See Also

- [Deployment](deployment.md) - корректная последовательность запуска
- [Operations](operations.md) - команды диагностики и runbook
- [Security](security.md) - настройка HTTPS и сертификатов
