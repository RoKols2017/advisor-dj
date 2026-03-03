[← Getting Started](getting-started.md) · [Back to README](../README.md) · [Architecture →](architecture.md)

# Configuration

## Основные переменные

| Переменная | Назначение | Пример |
|---|---|---|
| `DEBUG` | Режим отладки | `0` / `1` |
| `DJANGO_SETTINGS_MODULE` | Профиль Django | `config.settings.production` |
| `SECRET_KEY` | Ключ Django | длинная случайная строка |
| `ALLOWED_HOSTS` | Разрешенные хосты | `localhost,127.0.0.1,example.local` |
| `DATABASE_URL` | Подключение к БД | `postgres://advisor:***@db:5432/advisor` |

## Watcher и импорт

| Переменная | Назначение | Дефолт |
|---|---|---|
| `PRINT_EVENTS_WATCH_DIR` | Входящая папка | `/app/data/watch` |
| `PRINT_EVENTS_PROCESSED_DIR` | Успешные файлы | `/app/data/processed` |
| `PRINT_EVENTS_QUARANTINE_DIR` | Ошибочные файлы | `/app/data/quarantine` |
| `IMPORT_TOKEN` | Токен для импорт-эндпоинтов | `change-me` |
| `WATCHER_MAX_RETRIES` | Количество повторов | `5` |
| `WATCHER_BACKOFF_BASE` | База backoff, сек | `2` |
| `WATCHER_BACKOFF_MAX` | Максимум backoff, сек | `30` |
| `WATCHER_DEADLINE_SECONDS` | Лимит обработки файла | `300` |

## Рекомендуемый способ создать env

```bash
./scripts/generate_env.sh
./scripts/generate_env.sh --interactive
./scripts/generate_env.sh --production
```

## Production замечания

- Для production используйте `.env.prod` и `docker-compose.prod.yml`
- Никогда не коммитьте реальные секреты
- Проверяйте `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` перед релизом

## Источники правды

- Детальный справочник переменных: `ENV.md`
- Шаблон production env: `.env.prod.template`
- Проверка деплоя: `DEPLOYMENT_CHECKLIST.md`

## See Also

- [Getting Started](getting-started.md) - запуск с минимальной конфигурацией
- [Deployment](deployment.md) - env-файлы и compose в продакшне
- [Security](security.md) - HTTPS, CSRF и работа с сертификатами
