# Быстрая настройка Nginx Reverse Proxy

## Этап A: HTTP (для разработки и тестирования)

### Шаг 1: Создание сети (один раз)

```bash
make nginx-setup
# или вручную:
docker network create reverse-proxy-network
```

### Шаг 2: Запуск основного стека приложения

```bash
make up-build
# или
docker compose up --build -d
```

Убедитесь, что сервис `web` подключен к сети `reverse-proxy-network` (уже настроено в `docker-compose.yml`).

### Шаг 3: Запуск Nginx

```bash
make nginx-up
# или
docker compose -f docker-compose.proxy.yml up -d
```

### Шаг 4: Проверка работы

```bash
# Проверка healthcheck Nginx
curl http://localhost/health
# Должно вернуть: healthy

# Проверка Django через Nginx
curl http://localhost/health/
# Должно вернуть JSON с статусом Django

# Проверка главной страницы
curl http://localhost/
# Должна вернуться HTML-страница Django
```

### Шаг 5: Просмотр логов

```bash
# Логи Nginx
make nginx-logs
# или
docker compose -f docker-compose.proxy.yml logs -f nginx

# Логи Django
make logs-web
```

## Проверка конфигурации

```bash
# Проверка синтаксиса конфигурации Nginx
make nginx-test
# или
docker compose -f docker-compose.proxy.yml exec nginx nginx -t
```

## Остановка

```bash
# Остановить Nginx
make nginx-down

# Остановить весь стек
make down
```

## Что было настроено

1. ✅ **Конфигурация Nginx** (`infrastructure/nginx/conf.d/advisor.conf`):
   - Healthcheck endpoint на `/health`
   - Проксирование всех запросов к Django на порт 8000
   - Лимиты размера тела запроса (10MB)

2. ✅ **Django настройки** (`config/settings/production.py`, `docker.py`):
   - `USE_X_FORWARDED_HOST = True` - для правильной работы с Host header
   - `SECURE_PROXY_SSL_HEADER` - для будущего HTTPS

3. ✅ **Docker Compose**:
   - `web` сервис подключен к `reverse-proxy-network`
   - Порт 8000 не пробрасывается на хост (доступ только через Nginx)

## Следующие шаги (Этап B: HTTPS)

Когда будете готовы к настройке SSL/TLS:

1. Получить сертификаты от MS CA
2. Разместить их в `infrastructure/certs/server/`
3. Раскомментировать HTTPS блок в `infrastructure/nginx/conf.d/advisor.conf`
4. Раскомментировать порт 443 в `docker-compose.proxy.yml`
5. Настроить `CSRF_TRUSTED_ORIGINS` в `.env.prod`

Подробная инструкция: `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md`

