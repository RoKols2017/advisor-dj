---
title: "ENV Variables Reference"
type: reference
status: draft
last_verified: "2026-02-20"
verified_against_commit: "latest"
owner: "@rom"
---

[Back to README](../README.md) · [File Watcher Setup →](FILE_WATCHER_SETUP.md)

## Основные переменные окружения

| Переменная | Назначение | Пример/дефолт |
| --- | --- | --- |
| DEBUG | Режим отладки | `0` (prod), `1` (dev)
| DJANGO_SETTINGS_MODULE | Модуль настроек | `config.settings.production` (prod), `config.settings.development` (dev)
| SECRET_KEY | Секрет Django | длинная случайная строка (>=50)
| ALLOWED_HOSTS | Разрешённые хосты | `localhost,127.0.0.1,example.com`
| DATABASE_URL | Подключение к БД | `postgres://user:pass@db:5432/advisor`

## Логи

| Переменная | Назначение | Пример/дефолт |
| --- | --- | --- |
| LOG_TO_FILE | Писать логи в файл | `1` (prod) |
| LOG_TO_CONSOLE | Логи в stdout | `0` (prod), `1` (dev)
| LOG_DIR | Директория логов | `/app/logs`
| LOG_FILE_NAME | Имя файла логов | `project.log`
| WATCHER_LOG_FILE_NAME | Имя файла логов демона | `print_events_watcher.log`

## Импорт / Watcher

| Переменная | Назначение | Пример/дефолт |
| --- | --- | --- |
| PRINT_EVENTS_WATCH_DIR | Входная директория | `/app/data/watch`
| PRINT_EVENTS_PROCESSED_DIR | Успешные файлы | `/app/data/processed`
| PRINT_EVENTS_QUARANTINE_DIR | Карантин | `/app/data/quarantine`
| IMPORT_TOKEN | Обязательный токен для POST импортов (`/import/users/`, `/import/print-events/`) | `change-me`
| ENABLE_WINDOWS_AUTH | Backend Windows-авторизации | `0` (off)
| WATCHER_MAX_RETRIES | Кол-во повторов обработки файла | `5` |
| WATCHER_BACKOFF_BASE | База экспоненциальной задержки, сек | `2` |
| WATCHER_BACKOFF_MAX | Максимальная задержка между повторами, сек | `30` |
| WATCHER_DEADLINE_SECONDS | Дедлайн на обработку файла, сек | `300` |

## Ingest (systemd service для транзитных каталогов)

Эти переменные задаются в `/etc/default/advisor-ingest` (см. `infrastructure/systemd/advisor-ingest.env.example`).

| Переменная | Назначение | Пример/дефолт |
| --- | --- | --- |
| INBOX_ROOT | Корень транзитных каталогов | `/srv/advisor/inbox` |
| WATCH_DIR | Куда ingest кладет файлы для watcher | `/var/lib/docker/volumes/advisor-dj_data/_data/watch` |
| FAILED_DIR | Куда складывать неуспешные файлы | `/srv/advisor/inbox/_failed` |
| ARCHIVE_DIR | Архив успешно поставленных файлов | `/srv/advisor/inbox/_archive` |
| STATE_DIR | Состояние дедупликации | `/srv/advisor/ingest/state` |
| LOG_FILE | Лог ingest-процесса | `/srv/advisor/ingest/logs/ingest_mover.log` |
| LOCK_FILE | Файл блокировки от параллельных запусков | `/var/lock/advisor-ingest.lock` |
| MIN_AGE_SECONDS | Минимальный возраст файла перед обработкой | `20` |
| MAX_FILES_PER_RUN | Лимит файлов за запуск | `500` |
| SOURCES | Список источников | `dc print1 print2` |

## Безопасность (prod)

| Переменная | Назначение | Пример |
| --- | --- | --- |
| CSRF_TRUSTED_ORIGINS | Доверенные источники CSRF | `https://your-domain.com,https://www.your-domain.com`
| SECURE_PROXY_SSL_HEADER | Заголовок прокси для HTTPS | `HTTP_X_FORWARDED_PROTO,https`

### Prod шаблон
- Файл: `.env.prod.template` — заполнить и сохранить как `.env.prod` на проде.

## 🔐 Лучшие практики для паролей БД

### Передача секретов
- **В репозитории**: только шаблоны `.env.example`, `.env.prod.template` с плейсхолдерами (`__PASS__`, `__CHANGE_ME__`).
- **В проде**: секреты через `--env-file .env.prod` или `env_file: .env.prod` в compose.
- **Docker Secrets**: предпочтительно использовать `POSTGRES_PASSWORD_FILE` вместо переменных окружения.

### Пароли с особыми символами
- **Проблемные символы**: `#`, `@`, `:`, `%`, `&`, `+`, пробелы.
- **Решение 1**: URL-кодирование в `DATABASE_URL`:
  ```bash
  # Пароль: "my#pass@word" → "my%23pass%40word"
  DATABASE_URL=postgres://user:my%23pass%40word@db:5432/advisor
  ```
- **Решение 2**: кавычки в .env файле:
  ```bash
  POSTGRES_PASSWORD="my#pass@word"
  ```
- **Решение 3**: простые символы (a-z, A-Z, 0-9, !@$%^&*()_+-=[]{}|;:,.<>?)

### Безопасность
- Пароли не коммитить, не логировать, не печатать в CI.
- Проверять, что `DATABASE_URL` не попадает в логи приложения.
- Минимальные привилегии: отдельный пользователь БД для приложения.
- Разные пароли/базы в dev/prod; регулярная ротация паролей.

## See Also

- [Getting Started](getting-started.md) - базовый путь запуска
- [Deployment](deployment.md) - актуальный сценарий деплоя
- [Troubleshooting](troubleshooting.md) - диагностика типовых проблем
