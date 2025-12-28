# Пошаговый план внедрения Nginx Reverse Proxy

## Этап A: Подготовка (с интернетом)

### Шаг A1: Подготовка структуры каталогов

**Цель:** Создать структуру каталогов для конфигурации Nginx и сертификатов.

**Изменения:**
```bash
mkdir -p infrastructure/nginx/conf.d
mkdir -p infrastructure/nginx/snippets
mkdir -p infrastructure/certs/ca
mkdir -p infrastructure/certs/server
```

**Результат:**
- Структура каталогов создана
- Готово место для конфигов и сертификатов

**Проверка:**
```bash
tree infrastructure/ -L 3
```

---

### Шаг A2: Создание базовых конфигураций Nginx

**Цель:** Создать основные конфигурационные файлы Nginx.

**Файлы:**
1. `infrastructure/nginx/nginx.conf` — основной конфиг
2. `infrastructure/nginx/conf.d/default.conf` — базовые настройки
3. `infrastructure/nginx/snippets/` — общие snippets

**Содержимое `nginx.conf`:**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Включаем конфиги из conf.d
    include /etc/nginx/conf.d/*.conf;
}
```

**Содержимое `conf.d/default.conf`:**
```nginx
# Редирект HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Healthcheck endpoint без редиректа
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Всё остальное — редирект на HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}
```

**Содержимое `snippets/security-headers.conf`:**
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Содержимое `snippets/proxy-common.conf`:**
```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;

proxy_connect_timeout 10s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

**Содержимое `conf.d/advisor.conf`:**
```nginx
upstream advisor_backend {
    server advisor-web:8000;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name advisor.domain.local;

    # SSL конфигурация (заполнится на этапе B)
    ssl_certificate /etc/nginx/certs/server/advisor.domain.local.crt;
    ssl_certificate_key /etc/nginx/certs/server/advisor.domain.local.key;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    include /etc/nginx/snippets/security-headers.conf;
    
    # Лимиты
    client_max_body_size 10m;
    
    # Проксирование
    location / {
        include /etc/nginx/snippets/proxy-common.conf;
        proxy_pass http://advisor_backend;
    }
}
```

**Результат:**
- Все конфигурационные файлы созданы
- Nginx готов к запуску (кроме SSL сертификатов)

**Проверка синтаксиса (после запуска контейнера):**
```bash
docker compose -f docker-compose.proxy.yml exec nginx nginx -t
```

---

### Шаг A3: Создание docker-compose.proxy.yml

**Цель:** Создать отдельный docker-compose файл для Nginx.

**Файл:** `docker-compose.proxy.yml`

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    container_name: reverse-proxy-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infrastructure/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infrastructure/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./infrastructure/nginx/snippets:/etc/nginx/snippets:ro
      - ./infrastructure/certs:/etc/nginx/certs:ro
      - nginx-logs:/var/log/nginx
    networks:
      - reverse-proxy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  reverse-proxy-network:
    name: reverse-proxy-network
    external: true

volumes:
  nginx-logs:
```

**Результат:**
- docker-compose файл для Nginx создан
- Сеть `reverse-proxy-network` объявлена как external (создадим отдельно)

**Проверка:**
```bash
docker compose -f docker-compose.proxy.yml config
```

---

### Шаг A4: Создание сети reverse-proxy-network

**Цель:** Создать общую сеть для Nginx и всех backend-сервисов.

**Команда:**
```bash
docker network create reverse-proxy-network
```

**Результат:**
- Сеть создана
- Nginx и backend-сервисы смогут взаимодействовать через эту сеть

**Проверка:**
```bash
docker network ls | grep reverse-proxy-network
docker network inspect reverse-proxy-network
```

---

### Шаг A5: Модификация docker-compose.yml для advisor

**Цель:** Подключить advisor-web к сети reverse-proxy-network, убрать проброс портов на хост.

**Изменения в `docker-compose.yml`:**

1. Добавить network для web-сервиса:
```yaml
services:
  web:
    # ... существующие настройки ...
    networks:
      - advisor-network
      - reverse-proxy-network  # Добавить эту строку
    # Убрать или закомментировать ports (больше не нужно)
    # ports:
    #   - "${WEB_PORT:-8001}:8000"
```

2. Обновить секцию networks:
```yaml
networks:
  advisor-network:
    driver: bridge
  reverse-proxy-network:
    external: true
```

**Результат:**
- advisor-web доступен через Docker DNS для Nginx
- Порт 8001 на хосте больше не используется
- Приложение доступно только через Nginx

**Проверка:**
```bash
# Запустить стек
docker compose up -d

# Проверить сети
docker network inspect reverse-proxy-network | grep -A 5 advisor-web

# Проверить, что порт 8001 не слушается на хосте
sudo netstat -tlnp | grep 8001  # Не должно быть вывода
```

---

### Шаг A6: Обновление ALLOWED_HOSTS в Django

**Цель:** Добавить поддомен advisor.domain.local в ALLOWED_HOSTS.

**Изменения:**
В `.env` или `docker-compose.yml`:
```yaml
environment:
  - ALLOWED_HOSTS=${ALLOWED_HOSTS:-advisor.domain.local,localhost,127.0.0.1}
```

Или в `.env` файле:
```
ALLOWED_HOSTS=advisor.domain.local,localhost,127.0.0.1
```

**Результат:**
- Django принимает запросы с поддомена advisor.domain.local

**Проверка:**
```bash
docker compose exec web python manage.py check --deploy
# Должно быть без ошибок про ALLOWED_HOSTS
```

---

### Шаг A7: Запуск Nginx без SSL (тестирование)

**Цель:** Запустить Nginx и проверить работу без SSL (временный HTTP-only режим).

**Команды:**
```bash
# Временно закомментировать SSL-блоки в advisor.conf
# Или создать временный HTTP-only конфиг

# Запустить Nginx
docker compose -f docker-compose.proxy.yml up -d

# Проверить статус
docker compose -f docker-compose.proxy.yml ps

# Проверить логи
docker compose -f docker-compose.proxy.yml logs nginx

# Тест (если настроен /etc/hosts или DNS)
curl -H "Host: advisor.domain.local" http://localhost/
```

**Ожидаемый результат:**
- Nginx запущен
- Запросы проксируются к advisor-web
- Логи показывают успешные запросы

**Возможные ошибки:**
- `upstream not found` — проверить, что advisor-web в сети reverse-proxy-network
- `502 Bad Gateway` — проверить, что advisor-web запущен и отвечает на :8000

---

### Шаг A8: Создание заготовки для n8n (будущее)

**Цель:** Заложить конфигурацию для будущего добавления n8n.

**Файл:** `infrastructure/nginx/conf.d/n8n.conf` (закомментирован)

```nginx
# ЗАГОТОВКА для будущего развертывания n8n
# Раскомментировать после добавления n8n в docker-compose

# upstream n8n_backend {
#     server n8n-web:5678;
# }
#
# # n8n UI
# server {
#     listen 443 ssl http2;
#     server_name n8n.domain.local;
#     
#     ssl_certificate /etc/nginx/certs/server/n8n.domain.local.crt;
#     ssl_certificate_key /etc/nginx/certs/server/n8n.domain.local.key;
#     
#     include /etc/nginx/snippets/security-headers.conf;
#     client_max_body_size 10m;
#     
#     location / {
#         include /etc/nginx/snippets/proxy-common.conf;
#         proxy_pass http://n8n_backend;
#     }
# }
#
# # n8n Webhooks (длинные таймауты)
# server {
#     listen 443 ssl http2;
#     server_name n8n-webhooks.domain.local;
#     
#     ssl_certificate /etc/nginx/certs/server/n8n-webhooks.domain.local.crt;
#     ssl_certificate_key /etc/nginx/certs/server/n8n-webhooks.domain.local.key;
#     
#     include /etc/nginx/snippets/security-headers.conf;
#     client_max_body_size 100m;
#     
#     location / {
#         include /etc/nginx/snippets/proxy-common.conf;
#         proxy_read_timeout 300s;
#         proxy_send_timeout 300s;
#         proxy_pass http://n8n_backend;
#     }
# }
```

**Результат:**
- Заготовка создана
- При добавлении n8n достаточно раскомментировать и добавить сертификаты

---

## Этап B: Развертывание в ЛВС (без интернета)

### Шаг B1: Подготовка доверия к MS CA на хосте

**Цель:** Установить корневые/промежуточные сертификаты MS CA в систему доверия хоста.

**Предположения:**
- Сертификаты CA получены от администратора ЛВС
- Формат: `.crt` или `.cer` файлы

**Процедура на Ubuntu/Debian:**
```bash
# Скопировать CA сертификаты
sudo cp infrastructure/certs/ca/root-ca.crt /usr/local/share/ca-certificates/ms-root-ca.crt
sudo cp infrastructure/certs/ca/intermediate-ca.crt /usr/local/share/ca-certificates/ms-intermediate-ca.crt

# Обновить хранилище сертификатов
sudo update-ca-certificates

# Проверка
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt infrastructure/certs/ca/root-ca.crt
```

**Альтернатива (только для Docker):**
Можно не устанавливать на хост, а передать в Nginx через volume (см. шаг B2).

**Результат:**
- Система доверяет MS CA
- Можно валидировать сертификаты, выпущенные этим CA

**Проверка:**
```bash
# Проверить, что сертификат установлен
ls -la /etc/ssl/certs/ | grep ms

# Проверить цепочку (если есть тестовый сертификат)
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt infrastructure/certs/server/advisor.domain.local.crt
```

---

### Шаг B2: Установка серверных TLS сертификатов

**Цель:** Разместить сертификаты для advisor.domain.local в каталоге Nginx.

**Предположения:**
- Сертификат получен от администратора ЛВС
- Формат: `.crt` (сертификат) и `.key` (приватный ключ)

**Процедура:**
```bash
# Скопировать сертификаты
cp /path/to/advisor.domain.local.crt infrastructure/certs/server/
cp /path/to/advisor.domain.local.key infrastructure/certs/server/

# Установить правильные права
chmod 644 infrastructure/certs/server/advisor.domain.local.crt
chmod 600 infrastructure/certs/server/advisor.domain.local.key

# Владелец (опционально, если нужна изоляция)
chown root:root infrastructure/certs/server/advisor.domain.local.*
```

**Если нужна цепочка сертификатов:**
```bash
# Собрать fullchain.pem (если промежуточный CA используется)
cat infrastructure/certs/server/advisor.domain.local.crt \
    infrastructure/certs/ca/intermediate-ca.crt > \
    infrastructure/certs/server/fullchain.pem

# Использовать fullchain.pem в nginx.conf вместо .crt
```

**Результат:**
- Сертификаты размещены в правильных каталогах
- Права доступа установлены корректно

**Проверка:**
```bash
# Проверить сертификат
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -text -noout

# Проверить срок действия
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -noout -dates

# Проверить цепочку (если CA установлен)
openssl verify -CAfile infrastructure/certs/ca/root-ca.crt infrastructure/certs/server/advisor.domain.local.crt
```

---

### Шаг B3: Настройка Nginx для использования SSL

**Цель:** Обновить конфигурацию Nginx для работы с SSL сертификатами.

**Изменения:**
1. Убедиться, что пути к сертификатам правильные в `conf.d/advisor.conf`
2. (Опционально) Если используется промежуточный CA, добавить в `nginx.conf`:
```nginx
http {
    # ...
    ssl_trusted_certificate /etc/nginx/certs/ca/intermediate-ca.crt;
    # ...
}
```

**Результат:**
- Nginx настроен на использование SSL

**Проверка синтаксиса:**
```bash
docker compose -f docker-compose.proxy.yml exec nginx nginx -t
```

---

### Шаг B4: Перезапуск Nginx и включение TLS

**Цель:** Перезапустить Nginx с SSL конфигурацией.

**Команды:**
```bash
# Перезагрузить конфигурацию (без downtime)
docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload

# Или полный перезапуск
docker compose -f docker-compose.proxy.yml restart nginx

# Проверить статус
docker compose -f docker-compose.proxy.yml ps nginx

# Проверить логи
docker compose -f docker-compose.proxy.yml logs nginx | tail -20
```

**Результат:**
- Nginx работает с TLS
- HTTP редиректит на HTTPS

**Проверка:**
```bash
# Проверить HTTPS (если настроен DNS или /etc/hosts)
curl -k https://advisor.domain.local/health/
# Или с проверкой сертификата
curl --cacert infrastructure/certs/ca/root-ca.crt https://advisor.domain.local/health/

# Проверить редирект HTTP → HTTPS
curl -I http://advisor.domain.local/
# Должен быть 301 Location: https://...
```

---

### Шаг B5: Настройка Django для работы за прокси

**Цель:** Убедиться, что Django правильно обрабатывает заголовки от Nginx.

**Изменения в `config/settings/production.py` или `docker.py`:**
```python
# Убедиться, что эти настройки включены
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False  # Nginx уже делает редирект
```

**Результат:**
- Django правильно определяет HTTPS-соединения
- Правильно формирует абсолютные URL

**Проверка:**
```bash
# Проверить настройки Django
docker compose exec web python manage.py check --deploy

# Проверить, что Django видит HTTPS
docker compose exec web python manage.py shell
>>> from django.conf import settings
>>> settings.USE_X_FORWARDED_HOST
True
>>> settings.SECURE_PROXY_SSL_HEADER
('HTTP_X_FORWARDED_PROTO', 'https')
```

---

### Шаг B6: Финальная проверка

**Цель:** Проверить всю цепочку: клиент → Nginx → Django.

**Чек-лист:**
```bash
# 1. Все контейнеры запущены
docker compose ps
docker compose -f docker-compose.proxy.yml ps

# 2. Nginx слушает порты 80 и 443
sudo netstat -tlnp | grep nginx
# Или
docker compose -f docker-compose.proxy.yml exec nginx netstat -tlnp

# 3. Healthcheck Nginx работает
curl http://localhost/health

# 4. HTTP редиректит на HTTPS
curl -I http://advisor.domain.local/

# 5. HTTPS работает
curl -k https://advisor.domain.local/health/

# 6. Django приложение доступно
curl -k https://advisor.domain.local/

# 7. Логи без ошибок
docker compose -f docker-compose.proxy.yml logs nginx | grep -i error
docker compose logs web | tail -20
```

**Результат:**
- Все проверки пройдены
- Система работает в production режиме

---

## Процедуры сопровождения

### Обновление сертификатов

**Сценарий:** Сертификат истекает, нужно обновить.

**Процедура:**
```bash
# 1. Получить новые сертификаты от администратора ЛВС
# 2. Сделать бэкап старых
cp infrastructure/certs/server/advisor.domain.local.crt infrastructure/certs/server/advisor.domain.local.crt.bak
cp infrastructure/certs/server/advisor.domain.local.key infrastructure/certs/server/advisor.domain.local.key.bak

# 3. Установить новые сертификаты
cp /path/to/new/advisor.domain.local.crt infrastructure/certs/server/
cp /path/to/new/advisor.domain.local.key infrastructure/certs/server/
chmod 644 infrastructure/certs/server/advisor.domain.local.crt
chmod 600 infrastructure/certs/server/advisor.domain.local.key

# 4. Проверить сертификат
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -noout -dates

# 5. Перезагрузить Nginx (без downtime)
docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload

# 6. Проверить работу
curl -k https://advisor.domain.local/health/
```

**Скрипт:** Создать `scripts/update-ssl-cert.sh` для автоматизации (опционально).

---

### Добавление нового приложения

**Процедура:**
1. Добавить сервис в docker-compose.yml приложения
2. Подключить к `reverse-proxy-network`
3. Создать `infrastructure/nginx/conf.d/{app}.conf`
4. Выпустить сертификат для нового поддомена
5. Перезагрузить Nginx: `docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload`

**Детали:** См. раздел "Процедура добавления нового Django-приложения" в архитектурном документе.

---

### Ротация логов Nginx

**Вариант 1: На хосте через logrotate**
```bash
# /etc/logrotate.d/nginx-docker
/path/to/infrastructure/nginx/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker compose -f docker-compose.proxy.yml exec nginx nginx -s reopen
    endscript
}
```

**Вариант 2: Внутри контейнера (использовать named volume)**
Ротация через стандартные механизмы Nginx или cron-задачи внутри контейнера.

---

### Мониторинг и диагностика

**Проверка доступности upstream:**
```bash
# Изнутри контейнера Nginx
docker compose -f docker-compose.proxy.yml exec nginx wget -O- http://advisor-web:8000/health/
```

**Просмотр access логов:**
```bash
docker compose -f docker-compose.proxy.yml exec nginx tail -f /var/log/nginx/access.log
```

**Просмотр error логов:**
```bash
docker compose -f docker-compose.proxy.yml exec nginx tail -f /var/log/nginx/error.log
```

**Проверка конфигурации:**
```bash
docker compose -f docker-compose.proxy.yml exec nginx nginx -t
```

