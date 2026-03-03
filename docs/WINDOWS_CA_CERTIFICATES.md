---
title: "Получение и применение SSL сертификатов от Windows Server CA"
type: guide
status: draft
date: 2025-01-12
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

[← Nginx Implementation](NGINX_REVERSE_PROXY_IMPLEMENTATION.md) · [Back to README](../README.md) · [Project Analysis →](PROJECT_ANALYSIS.md)

# Получение и применение SSL сертификатов от Windows Server CA

## 📋 Оглавление

1. [Подготовка к запросу сертификата](#подготовка-к-запросу-сертификата)
2. [Запрос сертификата через веб-интерфейс Windows CA](#запрос-через-веб-интерфейс)
3. [Запрос сертификата через командную строку (certreq)](#запрос-через-командную-строку)
4. [Экспорт сертификата и приватного ключа](#экспорт-сертификата)
5. [Преобразование формата сертификата (если нужно)](#преобразование-формата)
6. [Размещение сертификатов в проекте](#размещение-сертификатов)
7. [Активация HTTPS в Nginx](#активация-https)
8. [Проверка работы HTTPS](#проверка-работы)
9. [Обновление сертификатов](#обновление-сертификатов)

---

## 🔧 Подготовка к запросу сертификата

### Требования

- Доступ к Windows Server с установленным Certificate Authority (CA)
- Права на запрос сертификатов (обычно есть у всех пользователей домена)
- Знание доменного имени или IP адреса сервера, где будет использоваться сертификат
- Доступ к серверу Linux, где развернут проект

### Информация для запроса сертификата

Перед запросом определите:

1. **Common Name (CN)** или **Subject Alternative Name (SAN)**:
   - Доменное имя: `advisor.domain.local` или `advisor.yourcompany.local`
   - Или IP адрес: `192.168.1.100`
   - Можно указать оба варианта в SAN

2. **Тип сертификата:**
   - **Web Server** или **Server Authentication**
   - Должен поддерживать **Server Authentication** (OID: 1.3.6.1.5.5.7.3.1)

3. **Формат экспорта:**
   - Сертификат: `.crt` или `.cer` (Base64 или DER)
   - Приватный ключ: `.key` или `.pfx` (PKCS#12)

---

## 🌐 Запрос через веб-интерфейс

### Шаг 1: Открыть веб-интерфейс Windows CA

1. Откройте браузер на компьютере в домене
2. Перейдите по адресу: `http://<CA-Server-Name>/certsrv`
   - Например: `http://dc01.company.local/certsrv`
3. Войдите с учетными данными домена

### Шаг 2: Запросить сертификат

1. Выберите **"Request a certificate"**
2. Выберите **"Advanced certificate request"**
3. Выберите **"Create and submit a request to this CA"**

### Шаг 3: Заполнить форму запроса

**В поле "Certificate Template":**
- Выберите **"Web Server"** или **"Server Authentication"**

**В поле "Identifying Information":**
- **Name:** `advisor.domain.local` (или ваш домен/IP)
- **Email:** (опционально)
- **Company:** (опционально)
- **Department:** (опционально)
- **City:** (опционально)
- **State:** (опционально)
- **Country/Region:** `RU` (или ваш код страны)

**В поле "Key Options":**
- **Key Size:** `2048` или `4096` (рекомендуется 2048)
- **Key Usage:** Отметьте **"Mark keys as exportable"** (важно!)
- **Create new key set:** Оставьте отмеченным

**В поле "Additional Options":**
- **Request Format:** `PKCS #10`
- **Hash Algorithm:** `SHA256` или `SHA512`

**В поле "Attributes":**
- Для SAN (Subject Alternative Name) добавьте:
  ```
  san:dns=advisor.domain.local&dns=advisor&ipaddress=192.168.1.100
  ```
  Или только DNS:
  ```
  san:dns=advisor.domain.local&dns=advisor
  ```

### Шаг 4: Отправить запрос

1. Нажмите **"Submit"**
2. Запомните **Request ID** (если показан)
3. Дождитесь одобрения администратором CA (если требуется)

### Шаг 5: Установить сертификат

1. Вернитесь на главную страницу CA
2. Выберите **"View the status of a pending certificate request"**
3. Найдите ваш запрос по Request ID или по имени
4. Если статус **"Issued"**, нажмите на него
5. Выберите **"Base 64 encoded"** или **"DER encoded"**
6. Нажмите **"Download certificate"**
7. Сохраните файл как `advisor.domain.local.cer` или `advisor.domain.local.crt`

---

## 💻 Запрос через командную строку (certreq)

### Шаг 1: Создать файл запроса (INF)

Создайте файл `cert-request.inf`:

```ini
[Version]
Signature="$Windows NT$"

[NewRequest]
Subject = "CN=advisor.domain.local, O=Your Company, C=RU"
KeySpec = 1
KeyLength = 2048
Exportable = TRUE
MachineKeySet = FALSE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
ProviderType = 12
RequestType = PKCS10

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "dns=advisor.domain.local&"
_continue_ = "dns=advisor&"
_continue_ = "ipaddress=192.168.1.100"

[RequestAttributes]
CertificateTemplate = "WebServer"
```

**Важные параметры:**
- `Subject = "CN=..."` — Common Name (домен или IP)
- `KeyLength = 2048` — длина ключа (2048 или 4096)
- `Exportable = TRUE` — **обязательно!** для экспорта приватного ключа
- `CertificateTemplate = "WebServer"` — шаблон сертификата

### Шаг 2: Создать запрос (REQ)

```cmd
certreq -new cert-request.inf cert-request.req
```

Это создаст файл `cert-request.req` (PKCS#10 запрос).

### Шаг 3: Отправить запрос в CA

**Вариант A: Через веб-интерфейс**
1. Откройте `http://<CA-Server>/certsrv`
2. Выберите **"Advanced certificate request"**
3. Выберите **"Submit a certificate request by using a base-64-encoded..."**
4. Откройте `cert-request.req` в текстовом редакторе
5. Скопируйте содержимое (включая `-----BEGIN CERTIFICATE REQUEST-----` и `-----END CERTIFICATE REQUEST-----`)
6. Вставьте в форму и отправьте

**Вариант B: Через командную строку (если есть доступ)**
```cmd
certreq -submit -config "CA-Server\CA-Name" cert-request.req advisor.domain.local.cer
```

### Шаг 4: Установить сертификат

```cmd
certreq -accept advisor.domain.local.cer
```

Или через веб-интерфейс CA (см. предыдущий раздел).

---

## 📤 Экспорт сертификата

### Шаг 1: Открыть хранилище сертификатов

1. Нажмите `Win + R`
2. Введите `certmgr.msc` и нажмите Enter
3. Перейдите в **"Personal" → "Certificates"**
4. Найдите сертификат для `advisor.domain.local`

### Шаг 2: Экспортировать сертификат

1. Правой кнопкой на сертификат → **"All Tasks" → "Export..."**
2. В мастере экспорта:
   - Выберите **"Yes, export the private key"** (если доступно)
   - Формат: **"Personal Information Exchange - PKCS #12 (.PFX)"**
   - Отметьте **"Include all certificates in the certification path if possible"**
   - Отметьте **"Export all extended properties"**
   - Введите пароль для защиты `.pfx` файла
   - Сохраните как `advisor.domain.local.pfx`

**Важно:** Если опция "Export the private key" недоступна, значит сертификат был установлен без возможности экспорта. Нужно запросить новый сертификат с флагом `Exportable = TRUE`.

### Шаг 3: Экспортировать только сертификат (без ключа)

Если нужно только сертификат (для проверки):

1. Правой кнопкой на сертификат → **"All Tasks" → "Export..."**
2. Выберите **"No, do not export the private key"**
3. Формат: **"Base-64 encoded X.509 (.CER)"**
4. Сохраните как `advisor.domain.local.cer`

---

## 🔄 Преобразование формата

### Из PFX в CRT и KEY (Linux)

После экспорта `.pfx` файла, преобразуйте его на Linux сервере:

```bash
# Установить OpenSSL (если не установлен)
sudo apt-get update && sudo apt-get install -y openssl

# Преобразовать PFX в PEM (сертификат + ключ)
openssl pkcs12 -in advisor.domain.local.pfx -nocerts -nodes -out advisor.domain.local.key
openssl pkcs12 -in advisor.domain.local.pfx -clcerts -nokeys -out advisor.domain.local.crt

# Или извлечь оба сразу
openssl pkcs12 -in advisor.domain.local.pfx -nodes -out advisor.domain.local.pem

# Затем разделить на отдельные файлы
openssl rsa -in advisor.domain.local.pem -out advisor.domain.local.key
openssl x509 -in advisor.domain.local.pem -out advisor.domain.local.crt
```

**Примечание:** При запросе пароля введите пароль, который вы указали при экспорте `.pfx`.

### Из CER в CRT

Если у вас `.cer` файл (Base64):

```bash
# Просто переименовать (формат уже правильный)
cp advisor.domain.local.cer advisor.domain.local.crt
```

Если `.cer` в формате DER:

```bash
# Преобразовать из DER в PEM
openssl x509 -inform DER -in advisor.domain.local.cer -out advisor.domain.local.crt
```

### Проверка формата

```bash
# Проверить формат файла
file advisor.domain.local.crt
# Должно быть: "PEM certificate" или "ASCII text"

# Просмотреть содержимое сертификата
openssl x509 -in advisor.domain.local.crt -text -noout

# Проверить приватный ключ
openssl rsa -in advisor.domain.local.key -check -noout
```

---

## 📁 Размещение сертификатов

### Шаг 1: Создать структуру каталогов

```bash
cd /home/oitroot/project/advisor-dj

# Создать каталоги (если не существуют)
mkdir -p infrastructure/certs/ca
mkdir -p infrastructure/certs/server
```

### Шаг 2: Скопировать сертификаты

```bash
# Скопировать сертификат и ключ
cp advisor.domain.local.crt infrastructure/certs/server/
cp advisor.domain.local.key infrastructure/certs/server/

# Если есть корневой сертификат CA (опционально)
cp root-ca.crt infrastructure/certs/ca/
cp intermediate-ca.crt infrastructure/certs/ca/  # если есть
```

### Шаг 3: Установить права доступа

```bash
# Сертификаты - только чтение для всех
chmod 644 infrastructure/certs/server/*.crt
chmod 644 infrastructure/certs/ca/*.crt 2>/dev/null || true

# Приватный ключ - только для владельца
chmod 600 infrastructure/certs/server/*.key

# Проверка прав
ls -la infrastructure/certs/server/
ls -la infrastructure/certs/ca/
```

**Ожидаемый результат:**
```
-rw-r--r-- 1 user user 1234 Jan 12 12:00 advisor.domain.local.crt
-rw------- 1 user user 1675 Jan 12 12:00 advisor.domain.local.key
```

### Шаг 4: Проверка сертификатов

```bash
# Проверить сертификат
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -text -noout

# Проверить срок действия
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -noout -dates

# Проверить приватный ключ
openssl rsa -in infrastructure/certs/server/advisor.domain.local.key -check -noout

# Проверить соответствие ключа и сертификата
openssl x509 -noout -modulus -in infrastructure/certs/server/advisor.domain.local.crt | openssl md5
openssl rsa -noout -modulus -in infrastructure/certs/server/advisor.domain.local.key | openssl md5
# Хеши должны совпадать!
```

---

## 🔒 Активация HTTPS в Nginx

### Шаг 1: Раскомментировать HTTPS блок в advisor.conf

Отредактируйте `infrastructure/nginx/conf.d/advisor.conf`:

1. Раскомментируйте HTTPS server блок (строки 38-72)
2. Раскомментируйте HTTP → HTTPS редирект (строки 75-91)
3. Обновите `server_name` на реальный домен/IP:

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name advisor.domain.local;  # Заменить на ваш домен
    
    # SSL сертификаты
    ssl_certificate /etc/nginx/certs/server/advisor.domain.local.crt;
    ssl_certificate_key /etc/nginx/certs/server/advisor.domain.local.key;
    
    # ... остальные настройки
}

# Редирект HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name advisor.domain.local;  # Заменить на ваш домен
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}
```

### Шаг 2: Раскомментировать порт 443 в docker-compose.proxy.yml

Отредактируйте `docker-compose.proxy.yml`:

```yaml
ports:
  - "80:80"
  - "443:443"  # Раскомментировать эту строку
```

### Шаг 3: Обновить настройки Django

В `.env` файле добавьте:

```env
CSRF_TRUSTED_ORIGINS=https://advisor.domain.local,https://192.168.1.100
```

Или если используете IP:

```env
CSRF_TRUSTED_ORIGINS=https://192.168.1.100
```

### Шаг 4: Перезапустить Nginx

```bash
# Проверить синтаксис конфигурации
docker compose -f docker-compose.proxy.yml exec nginx nginx -t

# Если синтаксис правильный, перезапустить
docker compose -f docker-compose.proxy.yml restart nginx

# Или перезагрузить конфигурацию без остановки
docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload

# Проверить статус
docker compose -f docker-compose.proxy.yml ps nginx
```

---

## ✅ Проверка работы HTTPS

### Проверка 1: Статус контейнера

```bash
docker compose -f docker-compose.proxy.yml ps nginx
# Должен быть статус "Up" и "healthy"
```

### Проверка 2: Прослушивание портов

```bash
# Проверить, что Nginx слушает порты 80 и 443
docker compose -f docker-compose.proxy.yml exec nginx netstat -tlnp | grep -E '80|443'
# Или с хоста
sudo netstat -tlnp | grep nginx
```

### Проверка 3: HTTPS endpoint

```bash
# Проверка без проверки сертификата (для теста)
curl -k https://advisor.domain.local/health/

# Проверка с проверкой сертификата (если CA установлен в системе)
curl https://advisor.domain.local/health/

# Или с указанием CA сертификата
curl --cacert infrastructure/certs/ca/root-ca.crt https://advisor.domain.local/health/
```

**Ожидаемый результат:**
```json
{"status":"healthy","checks":{"database":"ok","cache":"ok","application":"ok"}}
```

### Проверка 4: Редирект HTTP → HTTPS

```bash
# Проверить редирект
curl -I http://advisor.domain.local/
# Должен вернуть: HTTP/1.1 301 Moved Permanently
# И заголовок: Location: https://advisor.domain.local/
```

### Проверка 5: Информация о сертификате

```bash
# Просмотреть информацию о сертификате
echo | openssl s_client -connect advisor.domain.local:443 -servername advisor.domain.local 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# Проверить цепочку сертификатов
echo | openssl s_client -connect advisor.domain.local:443 -servername advisor.domain.local 2>/dev/null | openssl x509 -noout -text
```

### Проверка 6: Логи Nginx

```bash
# Проверить логи на ошибки
docker compose -f docker-compose.proxy.yml logs nginx | grep -i error

# Проверить access логи
docker compose -f docker-compose.proxy.yml logs nginx | tail -20
```

---

## 🔄 Обновление сертификатов

Когда сертификат истекает (обычно за 1-2 недели до истечения):

### Шаг 1: Запросить новый сертификат

Повторите процедуру запроса сертификата (см. разделы выше).

### Шаг 2: Сделать бэкап старых сертификатов

```bash
cd /home/oitroot/project/advisor-dj

# Создать бэкап
cp infrastructure/certs/server/advisor.domain.local.crt infrastructure/certs/server/advisor.domain.local.crt.bak.$(date +%Y%m%d)
cp infrastructure/certs/server/advisor.domain.local.key infrastructure/certs/server/advisor.domain.local.key.bak.$(date +%Y%m%d)
```

### Шаг 3: Установить новые сертификаты

```bash
# Скопировать новые сертификаты
cp /path/to/new/advisor.domain.local.crt infrastructure/certs/server/
cp /path/to/new/advisor.domain.local.key infrastructure/certs/server/

# Установить права
chmod 644 infrastructure/certs/server/advisor.domain.local.crt
chmod 600 infrastructure/certs/server/advisor.domain.local.key

# Проверить новый сертификат
openssl x509 -in infrastructure/certs/server/advisor.domain.local.crt -noout -dates
```

### Шаг 4: Перезагрузить Nginx (без downtime)

```bash
# Перезагрузить конфигурацию без остановки
docker compose -f docker-compose.proxy.yml exec nginx nginx -s reload

# Проверить работу
curl -k https://advisor.domain.local/health/
```

### Шаг 5: Удалить старые бэкапы (опционально)

После проверки работы можно удалить старые бэкапы:

```bash
# Удалить бэкапы старше 30 дней
find infrastructure/certs/server/ -name "*.bak.*" -mtime +30 -delete
```

---

## 🛠️ Решение проблем

### Проблема: "SSL certificate problem"

**Причина:** Браузер не доверяет CA.

**Решение:**
1. Установить корневой сертификат CA в систему доверия браузера
2. Или использовать сертификат от публичного CA (Let's Encrypt) для внешнего доступа

### Проблема: "Private key does not match certificate"

**Причина:** Несоответствие приватного ключа и сертификата.

**Решение:**
```bash
# Проверить соответствие
openssl x509 -noout -modulus -in advisor.domain.local.crt | openssl md5
openssl rsa -noout -modulus -in advisor.domain.local.key | openssl md5
# Хеши должны совпадать!

# Если не совпадают - нужно экспортировать правильный ключ из Windows
```

### Проблема: "Certificate has expired"

**Причина:** Сертификат истек.

**Решение:** Обновить сертификат (см. раздел "Обновление сертификатов").

### Проблема: Nginx не запускается после добавления HTTPS

**Причина:** Ошибка в конфигурации или отсутствие сертификатов.

**Решение:**
```bash
# Проверить синтаксис
docker compose -f docker-compose.proxy.yml exec nginx nginx -t

# Проверить логи
docker compose -f docker-compose.proxy.yml logs nginx

# Проверить наличие сертификатов
docker compose -f docker-compose.proxy.yml exec nginx ls -la /etc/nginx/certs/server/
```

---

## 📚 Дополнительные ресурсы

- [Документация Nginx SSL](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Windows Certificate Services](https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
- [OpenSSL документация](https://www.openssl.org/docs/)

---

## 📝 Чеклист развертывания HTTPS

- [ ] Получен сертификат от Windows Server CA
- [ ] Экспортирован приватный ключ (с флагом Exportable)
- [ ] Преобразованы форматы (PFX → CRT/KEY, если нужно)
- [ ] Сертификаты размещены в `infrastructure/certs/server/`
- [ ] Установлены правильные права доступа (644 для CRT, 600 для KEY)
- [ ] Проверено соответствие ключа и сертификата
- [ ] Раскомментирован HTTPS блок в `advisor.conf`
- [ ] Обновлен `server_name` на реальный домен
- [ ] Раскомментирован порт 443 в `docker-compose.proxy.yml`
- [ ] Добавлен `CSRF_TRUSTED_ORIGINS` в `.env`
- [ ] Перезапущен Nginx
- [ ] Проверена работа HTTPS
- [ ] Проверен редирект HTTP → HTTPS
- [ ] Проверены логи на ошибки

---

*Последнее обновление: 2025-01-12*

## See Also

- [Getting Started](getting-started.md) - базовый путь запуска
- [Deployment](deployment.md) - актуальный сценарий деплоя
- [Troubleshooting](troubleshooting.md) - диагностика типовых проблем
