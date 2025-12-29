# Сертификаты SSL/TLS для Nginx

## Структура каталогов

```
infrastructure/certs/
├── ca/              # Сертификаты CA (корневые и промежуточные)
│   ├── root-ca.crt
│   └── intermediate-ca.crt
└── server/          # Серверные сертификаты
    ├── advisor.domain.local.crt
    └── advisor.domain.local.key
```

## Этап B: Настройка SSL/TLS

### Шаг 1: Получение сертификатов

Получите сертификаты от администратора ЛВС (MS CA):
- Корневой сертификат CA → `ca/root-ca.crt`
- Промежуточный сертификат CA (если есть) → `ca/intermediate-ca.crt`
- Серверный сертификат → `server/advisor.domain.local.crt`
- Приватный ключ → `server/advisor.domain.local.key`

### Шаг 2: Размещение сертификатов

```bash
# Скопировать сертификаты в соответствующие каталоги
cp /path/to/root-ca.crt infrastructure/certs/ca/
cp /path/to/intermediate-ca.crt infrastructure/certs/ca/  # если есть
cp /path/to/advisor.domain.local.crt infrastructure/certs/server/
cp /path/to/advisor.domain.local.key infrastructure/certs/server/

# Установить правильные права доступа
chmod 644 infrastructure/certs/server/*.crt
chmod 600 infrastructure/certs/server/*.key
```

### Шаг 3: Проверка сертификатов

```bash
# Проверить сертификат
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -text -noout

# Проверить срок действия
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -noout -dates

# Проверить цепочку (если CA установлен)
openssl verify -CAfile infrastructure/certs/ca/root-ca.crt infrastructure/certs/server/advisor.domain.local.crt
```

### Шаг 4: Активация HTTPS в Nginx

1. Раскомментировать HTTPS блок в `infrastructure/nginx/conf.d/advisor.conf`
2. Раскомментировать порт 443 в `docker-compose.proxy.yml`
3. Обновить `server_name` на реальный домен
4. Перезапустить Nginx: `make nginx-down && make nginx-up`

### Шаг 5: Настройка Django

В `.env.prod` добавить:
```env
CSRF_TRUSTED_ORIGINS=https://advisor.domain.local
```

Подробная инструкция: `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md` (Этап B)

## Безопасность

⚠️ **Важно:**
- Приватные ключи (`*.key`) должны иметь права `600` (только владелец)
- Сертификаты должны быть доступны только для чтения (`644`)
- Не коммитить приватные ключи в Git (добавьте `*.key` в `.gitignore`)
- Хранить резервные копии сертификатов в безопасном месте

## Обновление сертификатов

Когда сертификат истекает:

1. Получить новые сертификаты
2. Сделать бэкап старых
3. Установить новые (см. Шаг 2)
4. Перезагрузить Nginx: `docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload`

