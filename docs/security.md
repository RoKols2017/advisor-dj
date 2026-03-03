[← Testing](testing.md) · [Back to README](../README.md) · [Troubleshooting →](troubleshooting.md)

# Security

## Базовые правила

- Храните секреты только в `.env`/`.env.prod` вне git
- Не печатайте `DATABASE_URL`, `SECRET_KEY`, `IMPORT_TOKEN` в логах
- Используйте отдельные значения для dev и prod

## HTTPS в production

1. Получите сертификат для домена (например, из Windows Server CA)
2. Разместите `*.crt` и `*.key` в `infrastructure/certs/server/`
3. Настройте `server_name` и включите 443 в `docker-compose.proxy.yml`
4. Добавьте доверенные источники в `CSRF_TRUSTED_ORIGINS`

Проверка:

```bash
curl -I http://advisor.domain.local/
curl --cacert infrastructure/certs/ca/root-ca.crt https://advisor.domain.local/health/
```

## CSRF и хосты

- `ALLOWED_HOSTS` должен содержать реальные адреса сервера
- `CSRF_TRUSTED_ORIGINS` должен содержать HTTPS origin-ы
- Для reverse proxy учитывайте `SECURE_PROXY_SSL_HEADER`

## Что объединено в этот документ

Содержимое из прежнего root-файла:
- `ENABLE_HTTPS.md`

Оригинал оставлен в корне до финальной очистки.

## See Also

- [Configuration](configuration.md) - переменные безопасности
- [Deployment](deployment.md) - включение Nginx/HTTPS в проде
- [Troubleshooting](troubleshooting.md) - типичные ошибки TLS и прокси
