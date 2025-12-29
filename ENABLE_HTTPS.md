# Включение HTTPS для Print Advisor

## Текущая ситуация

Сейчас приложение работает через **HTTP (порт 80)** - это **Этап A** (разработка/тестирование).

Для включения **HTTPS (порт 443)** нужны SSL/TLS сертификаты от MS CA - это **Этап B** (production).

## Что нужно для HTTPS

### 1. Получить сертификаты от администратора ЛВС (MS CA)

Вам нужны:
- **Серверный сертификат** (`.crt`) для вашего домена
- **Приватный ключ** (`.key`) для сертификата
- **Корневой сертификат CA** (опционально, для проверки цепочки)

### 2. Разместить сертификаты

```bash
# Скопировать сертификаты
cp /path/to/your-cert.crt infrastructure/certs/server/advisor.domain.local.crt
cp /path/to/your-key.key infrastructure/certs/server/advisor.domain.local.key
cp /path/to/ca-root.crt infrastructure/certs/ca/root-ca.crt  # если есть

# Установить права доступа
chmod 644 infrastructure/certs/server/*.crt
chmod 600 infrastructure/certs/server/*.key
```

### 3. Раскомментировать HTTPS конфигурацию

#### 3.1. В `infrastructure/nginx/conf.d/advisor.conf`

Раскомментировать блоки:
- HTTPS server блок (строки 38-72)
- HTTP → HTTPS редирект (строки 75-91)

И обновить `server_name` на реальный домен:
```nginx
server_name advisor.domain.local;  # заменить на ваш домен
```

#### 3.2. В `docker-compose.proxy.yml`

Раскомментировать порт 443:
```yaml
ports:
  - "80:80"
  - "443:443"  # раскомментировать эту строку
```

### 4. Обновить настройки Django

В `.env` или `.env.prod` добавить:
```env
CSRF_TRUSTED_ORIGINS=https://advisor.domain.local,https://your-ip
```

### 5. Перезапустить Nginx

```bash
sg docker -c "docker compose -f docker-compose.proxy.yml down"
sg docker -c "docker compose -f docker-compose.proxy.yml up -d"
```

Или через Makefile (если есть права):
```bash
make nginx-down
make nginx-up
```

## Проверка HTTPS

После настройки:

```bash
# Проверка HTTPS
curl -k https://advisor.domain.local/health/
# или с проверкой сертификата
curl --cacert infrastructure/certs/ca/root-ca.crt https://advisor.domain.local/health/

# Проверка редиректа HTTP → HTTPS
curl -I http://advisor.domain.local/
# Должен вернуть: 301 Location: https://...
```

## Альтернатива: Self-signed сертификат (только для тестирования)

Если нужен HTTPS для тестирования без MS CA:

```bash
# Создать self-signed сертификат (НЕ для production!)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infrastructure/certs/server/advisor.domain.local.key \
  -out infrastructure/certs/server/advisor.domain.local.crt \
  -subj "/C=RU/ST=State/L=City/O=Org/CN=advisor.domain.local"

chmod 644 infrastructure/certs/server/*.crt
chmod 600 infrastructure/certs/server/*.key
```

⚠️ **Внимание:** Self-signed сертификаты не подходят для production! Браузеры будут показывать предупреждение о безопасности.

## Текущий статус

- ✅ HTTP работает (порт 80)
- ⏳ HTTPS требует сертификаты от MS CA
- 📝 Конфигурация готова, нужно только раскомментировать и добавить сертификаты

## Документация

Подробная инструкция: `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md` (Этап B)

