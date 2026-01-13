# Включение HTTPS для Print Advisor

## Текущая ситуация

Сейчас приложение работает через **HTTP (порт 80)** - это **Этап A** (разработка/тестирование).

Для включения **HTTPS (порт 443)** нужны SSL/TLS сертификаты от Windows Server CA - это **Этап B** (production).

## 📚 Подробная инструкция

**👉 Полная инструкция по получению и применению сертификатов от Windows Server CA:**
**[docs/WINDOWS_CA_CERTIFICATES.md](docs/WINDOWS_CA_CERTIFICATES.md)**

Эта инструкция содержит:
- Запрос сертификата через веб-интерфейс Windows CA
- Запрос через командную строку (certreq)
- Экспорт сертификата и приватного ключа
- Преобразование форматов (PFX → CRT/KEY)
- Размещение и активация в Nginx
- Проверка и обновление сертификатов

## Что нужно для HTTPS

### 1. Получить сертификаты от Windows Server CA

**Подробная инструкция:** `docs/WINDOWS_CA_CERTIFICATES.md`

**Кратко:**
1. Откройте `http://<CA-Server>/certsrv`
2. Запросите сертификат типа **"Web Server"**
3. Укажите домен: `advisor.domain.local`
4. **Важно:** Отметьте **"Mark keys as exportable"**
5. Экспортируйте в формате `.pfx` с приватным ключом

Вам нужны:
- **Серверный сертификат** (`.crt`) для вашего домена
- **Приватный ключ** (`.key`) для сертификата
- **Корневой сертификат CA** (опционально, для проверки цепочки)

### 2. Преобразовать формат (если получили PFX)

Если получили `.pfx` файл от Windows:

```bash
# Преобразовать PFX в CRT и KEY
openssl pkcs12 -in advisor.domain.local.pfx -nocerts -nodes -out advisor.domain.local.key
openssl pkcs12 -in advisor.domain.local.pfx -clcerts -nokeys -out advisor.domain.local.crt
```

### 3. Разместить сертификаты

```bash
# Скопировать сертификаты
cp advisor.domain.local.crt infrastructure/certs/server/
cp advisor.domain.local.key infrastructure/certs/server/
cp /path/to/ca-root.crt infrastructure/certs/ca/root-ca.crt  # если есть

# Установить права доступа
chmod 644 infrastructure/certs/server/*.crt
chmod 600 infrastructure/certs/server/*.key

# Проверить соответствие ключа и сертификата
openssl x509 -noout -modulus -in infrastructure/certs/server/advisor.domain.local.crt | openssl md5
openssl rsa -noout -modulus -in infrastructure/certs/server/advisor.domain.local.key | openssl md5
# Хеши должны совпадать!
```

### 4. Раскомментировать HTTPS конфигурацию

#### 4.1. В `infrastructure/nginx/conf.d/advisor.conf`

Раскомментировать блоки:
- HTTPS server блок (строки 38-72)
- HTTP → HTTPS редирект (строки 75-91)

И обновить `server_name` на реальный домен:
```nginx
server_name advisor.domain.local;  # заменить на ваш домен
```

#### 4.2. В `docker-compose.proxy.yml`

Раскомментировать порт 443:
```yaml
ports:
  - "80:80"
  - "443:443"  # раскомментировать эту строку
```

### 5. Обновить настройки Django

В `.env` или `.env.prod` добавить:
```env
CSRF_TRUSTED_ORIGINS=https://advisor.domain.local,https://your-ip
```

### 6. Перезапустить Nginx

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

- **Полная инструкция по сертификатам:** `docs/WINDOWS_CA_CERTIFICATES.md`
- **Настройка Nginx:** `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md` (Этап B)
- **Сертификаты:** `infrastructure/certs/README.md`

