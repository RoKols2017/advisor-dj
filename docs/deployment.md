[← Architecture](architecture.md) · [Back to README](../README.md) · [Operations →](operations.md)

# Deployment

## Docker production стек

```bash
./scripts/generate_env.sh --production
mkdir -p data/{watch,processed,quarantine}
sudo chmod 777 data/{watch,processed,quarantine}
docker network create reverse-proxy-network
docker compose -f docker-compose.proxy.yml up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod build
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py migrate
docker compose -f docker-compose.prod.yml --env-file .env.prod exec web python manage.py createsuperuser
```

Проверка:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.proxy.yml ps
curl http://localhost/health
SMOKE_COMPOSE_FILE=docker-compose.prod.yml ./scripts/smoke.sh
```

## Развертывание в ЛВС без интернета

На машине с интернетом:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod build
docker save advisor-dj-web:latest advisor-dj-watcher:latest postgres:15 -o advisor-dj-images.tar
```

На целевой машине:

```bash
docker load -i advisor-dj-images.tar
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Автозапуск после перезагрузки

```bash
sudo cp advisor-dj.service /etc/systemd/system/
sudo sed -i 's|^WorkingDirectory=.*|WorkingDirectory=/path/to/advisor-dj|' /etc/systemd/system/advisor-dj.service
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service
```

## HTTPS и Nginx

1. Получите сертификаты (MS CA или другой доверенный источник)
2. Разместите сертификат и ключ в `infrastructure/certs/server/`
3. Включите HTTPS-конфиг в `infrastructure/nginx/conf.d/advisor.conf`
4. Перезапустите proxy стек

Подробности: `WINDOWS_CA_CERTIFICATES.md` и `NGINX_REVERSE_PROXY_IMPLEMENTATION.md`.

## Что объединено в этот документ

Содержимое из прежних root-файлов:
- `DEPLOY_NOW.md`
- `QUICK_DEPLOY.md`
- `SETUP.md`
- `DEPLOYMENT_SUMMARY.md`

Оригиналы оставлены в корне до финальной очистки.

## See Also

- [Configuration](configuration.md) - настройки env для деплоя
- [Operations](operations.md) - ежедневные команды поддержки
- [Troubleshooting](troubleshooting.md) - ошибки Docker, Nginx и доступов
