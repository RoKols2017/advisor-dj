# Быстрый запуск Nginx

## Проблема
Приложение недоступно в браузере, потому что порт закомментирован и доступ только через Nginx, но Nginx не запущен.

## Решение

### Вариант 1: Автоматический запуск (рекомендуется)

```bash
./scripts/start-nginx.sh
```

Скрипт проверит:
- Существование сети `reverse-proxy-network`
- Запущен ли контейнер `advisor-web`
- Подключен ли контейнер к сети
- Запустит Nginx

### Вариант 2: Ручной запуск

#### Шаг 1: Проверка сети
```bash
# С sudo (если нет прав)
sudo docker network ls | grep reverse-proxy-network

# Если сети нет, создайте:
sudo docker network create reverse-proxy-network
```

#### Шаг 2: Проверка основного стека
```bash
# Проверить статус
sudo docker compose ps

# Если контейнеры не запущены:
sudo docker compose up -d

# Убедиться, что web подключен к сети reverse-proxy-network
sudo docker inspect advisor-web | grep -A 10 "Networks"
```

#### Шаг 3: Запуск Nginx
```bash
# Запустить Nginx
sudo docker compose -f docker-compose.proxy.yml up -d

# Проверить статус
sudo docker compose -f docker-compose.proxy.yml ps
```

#### Шаг 4: Проверка работы
```bash
# Healthcheck Nginx
curl http://localhost/health
# Должно вернуть: healthy

# Healthcheck Django через Nginx
curl http://localhost/health/
# Должно вернуть JSON с статусом

# Главная страница
curl http://localhost/
# Должна вернуться HTML-страница
```

## Если контейнер web не подключен к сети

Если контейнер `advisor-web` не подключен к сети `reverse-proxy-network`, перезапустите основной стек:

```bash
sudo docker compose down
sudo docker compose up -d
```

Это переподключит контейнер к сети.

## Просмотр логов

```bash
# Логи Nginx
sudo docker compose -f docker-compose.proxy.yml logs -f nginx

# Логи Django
sudo docker compose logs -f web

# Все логи
sudo docker compose logs -f
```

## Остановка Nginx

```bash
sudo docker compose -f docker-compose.proxy.yml down
```

## Доступ к приложению

После запуска Nginx приложение доступно по адресу:
- `http://localhost/` (или IP адрес из ALLOWED_HOSTS)
- `http://10.85.1.59/` (ваш IP из .env)

Порт 80 должен быть открыт в firewall, если доступ извне.

