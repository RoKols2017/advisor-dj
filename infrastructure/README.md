# Инфраструктура Nginx Reverse Proxy

## Структура

```
infrastructure/
├── nginx/
│   ├── nginx.conf              # Основной конфиг Nginx
│   ├── conf.d/
│   │   ├── default.conf        # Healthcheck endpoint
│   │   ├── advisor.conf        # Конфигурация для advisor приложения
│   │   └── n8n.conf            # Заготовка для n8n (закомментирована)
│   └── snippets/
│       ├── security-headers.conf   # Заголовки безопасности
│       ├── proxy-common.conf       # Общие настройки проксирования
│       └── ssl-common.conf         # Общие SSL настройки (для этапа B)
└── certs/
    ├── ca/                        # Сертификаты CA (MS CA)
    └── server/                    # Серверные сертификаты
```

## Этап A (разработка, HTTP-only)

**Текущее состояние:**
- Nginx работает на порту 80 (HTTP)
- Доступ через `http://localhost/` или `http://<IP>/`
- SSL сертификаты не требуются

**Запуск:**
```bash
# Создать сеть (один раз)
docker network create reverse-proxy-network

# Запустить Nginx
docker compose -f docker-compose.proxy.yml up -d

# Запустить приложение
docker compose up -d
```

**Проверка:**
```bash
# Healthcheck Nginx
curl http://localhost/health

# Доступ к приложению
curl http://localhost/
```

## Этап B (production, HTTPS)

**После переноса в ЛВС:**
1. Установить сертификаты MS CA в `infrastructure/certs/ca/`
2. Установить серверные сертификаты в `infrastructure/certs/server/`
3. Раскомментировать SSL блоки в конфигах
4. Добавить порт 443 в `docker-compose.proxy.yml`
5. Перезапустить Nginx

**См. подробную документацию:** `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md`

