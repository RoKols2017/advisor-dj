---
title: "Архитектура Nginx Reverse Proxy для инфраструктуры"
type: guide
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Архитектура Nginx Reverse Proxy для инфраструктуры

## Обзор

Nginx работает в отдельном контейнере как единая точка входа (порты 80/443 на хосте), проксируя запросы к backend-сервисам через Docker DNS.

---

## Схема сетей и сервисов

```
┌─────────────────────────────────────────────────────────┐
│                      Docker Host                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │        reverse-proxy network (shared)             │  │
│  │                                                   │  │
│  │  ┌──────────────┐                                │  │
│  │  │   nginx      │  :443 (HTTPS)                   │  │
│  │  │  (proxy)     │  :80  (HTTP → HTTPS redirect)  │  │
│  │  └──────┬───────┘                                │  │
│  │         │ proxy_pass                              │  │
│  │         ▼                                         │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │      advisor-network (app-specific)       │    │  │
│  │  │  ┌──────────┐  ┌──────────┐             │    │  │
│  │  │  │advisor-web│  │advisor-db│             │    │  │
│  │  │  │  :8000   │  │  :5432   │             │    │  │
│  │  │  └──────────┘  └──────────┘             │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  │                                                   │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │      n8n-network (future)                 │    │  │
│  │  │  ┌──────────┐  ┌──────────┐             │    │  │
│  │  │  │n8n-web   │  │redis     │             │    │  │
│  │  │  │n8n-worker│  │          │             │    │  │
│  │  │  └──────────┘  └──────────┘             │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Две сети Docker:

1. **`reverse-proxy-network`** (external: true)
   - Общая сеть для Nginx и всех backend-сервисов
   - Nginx подключается к этой сети
   - Каждое приложение подключает свои сервисы к этой сети

2. **`advisor-network`** (app-specific)
   - Изолированная сеть для сервисов advisor (web, db, watcher)
   - Nginx НЕ подключен к этой сети
   - Используется для внутренней коммуникации между сервисами приложения

---

## Маршрутизация (поддомены)

| Поддомен | Upstream | Описание |
|----------|----------|----------|
| `advisor.domain.local` | `advisor-web:8000` | Django приложение advisor |
| `n8n.domain.local` | `n8n-web:5678` | n8n UI (будущее) |
| `n8n-webhooks.domain.local` | `n8n-web:5678` | n8n webhooks (будущее, длинные таймауты) |

**Почему поддомены, а не пути?**
- Проще изолировать сертификаты (один сертификат на поддомен или wildcard)
- Чище маршрутизация в Nginx
- Меньше конфликтов с путями внутри приложений (`/static`, `/admin`, `/api`)

---

## DNS резолюция в Docker

Nginx использует Docker DNS для поиска upstream-сервисов:

```nginx
upstream advisor_backend {
    server advisor-web:8000;
}
```

Где `advisor-web` — это имя контейнера или service name из docker-compose.

**Важно:** Оба сервиса (nginx и advisor-web) должны быть в одной сети (`reverse-proxy-network`).

---

## Статические файлы

**Подход:** Статические файлы отдаёт само Django-приложение через WhiteNoise или Nginx может проксировать `/static/` напрямую к upstream.

**Выбор:** Оставляем отдачу статики через Django (уже работает, collectstatic выполняется при сборке). В будущем, если потребуется оптимизация — можно добавить volume со staticfiles и отдавать напрямую из Nginx.

---

## Структура файлов и каталогов

```
advisor-dj/
├── docker-compose.yml              # Основной стек advisor
├── docker-compose.proxy.yml        # Nginx reverse proxy (отдельный файл)
├── infrastructure/                 # Общие инфраструктурные компоненты
│   ├── nginx/
│   │   ├── nginx.conf              # Основной конфиг
│   │   ├── conf.d/
│   │   │   ├── default.conf        # Базовые настройки (security headers, limits)
│   │   │   ├── advisor.conf        # Конфиг для advisor.domain.local
│   │   │   └── n8n.conf            # Конфиг для n8n (будущее, заготовка)
│   │   └── snippets/
│   │       ├── security-headers.conf
│   │       ├── ssl-common.conf
│   │       └── proxy-common.conf
│   └── certs/                      # Сертификаты TLS (НЕ в git!)
│       ├── ca/
│       │   ├── root-ca.crt         # Корневой CA от MS
│       │   └── intermediate-ca.crt # Промежуточный CA (если есть)
│       └── server/
│           ├── advisor.domain.local.crt
│           ├── advisor.domain.local.key
│           └── fullchain.pem       # Если нужна цепочка
├── scripts/
│   └── update-ssl-cert.sh          # Скрипт для обновления сертификатов
└── docs/
    └── nginx-reverse-proxy.md      # Эта документация
```

**Почему отдельный docker-compose.proxy.yml?**
- Nginx — инфраструктурный компонент, независимый от приложений
- Можно управлять отдельно (перезапуск Nginx не требует пересборки приложений)
- Проще масштабировать: добавлять новые приложения не трогая proxy-stack

---

## Volumes для Nginx

1. **`nginx-config`** (bind mount `./infrastructure/nginx/`)
   - Конфигурационные файлы
   - Обновление без пересборки образа (volume mount)

2. **`nginx-certs`** (bind mount `./infrastructure/certs/`)
   - TLS сертификаты и ключи
   - CA сертификаты
   - Права доступа: 644 для .crt, 600 для .key (на хосте)

3. **`nginx-logs`** (named volume или bind mount)
   - Access logs: `/var/log/nginx/access.log`
   - Error logs: `/var/log/nginx/error.log`
   - Ротация через logrotate на хосте или внутри контейнера

---

## Безопасность и заголовки

**Обязательные заголовки:**
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (или SAMEORIGIN если нужны iframe)
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

**Проксирование заголовков:**
- `X-Forwarded-Proto: $scheme`
- `X-Forwarded-Host: $host`
- `X-Forwarded-For: $proxy_add_x_forwarded_for`
- `X-Real-IP: $remote_addr`

---

## Лимиты и таймауты (важно для n8n webhooks)

**Базовые лимиты:**
- `client_max_body_size: 10m` (для обычных приложений)
- `proxy_read_timeout: 60s`
- `proxy_connect_timeout: 10s`

**Для n8n webhooks (отдельный location):**
- `client_max_body_size: 100m`
- `proxy_read_timeout: 300s` (5 минут для длинных webhook-запросов)
- `proxy_send_timeout: 300s`

---

## Healthcheck для Nginx

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 10s
  timeout: 5s
  retries: 3
```

Создаём endpoint `/health` в Nginx, который проверяет доступность upstream-сервисов.

---

## Именование контейнеров и сервисов

**Правило:**
- Контейнеры: `{app}-{service}` (например: `advisor-web`, `n8n-web`)
- Сервисы в docker-compose: `{app}-{service}` (для согласованности)
- Сети: `{app}-network` (для изоляции), `reverse-proxy-network` (общая)
- Домены: `{app}.domain.local`

---

## Процедура добавления нового Django-приложения

1. Добавить service в `docker-compose.yml` приложения
2. Подключить сервис к `reverse-proxy-network`:
   ```yaml
   networks:
     - reverse-proxy-network
   ```
3. Создать файл конфигурации `infrastructure/nginx/conf.d/{app}.conf`
4. Добавить upstream в конфиг
5. Добавить server block с server_name
6. Перезагрузить Nginx: `docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload`
7. (Опционально) Выпустить сертификат для нового поддомена

**Никаких изменений в основном конфиге Nginx не требуется.**

