---
title: "ENV Variables Reference"
type: reference
status: draft
last_verified: "2025-09-30"
owner: "@rom"
---

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
| IMPORT_TOKEN | Токен импорта (если нужен) | `change-me`
| ENABLE_WINDOWS_AUTH | Backend Windows-авторизации | `0` (off)

## Безопасность (prod)

| Переменная | Назначение | Пример |
| --- | --- | --- |
| CSRF_TRUSTED_ORIGINS | Доверенные источники CSRF | `https://your-domain.com,https://www.your-domain.com`
| SECURE_PROXY_SSL_HEADER | Заголовок прокси для HTTPS | `HTTP_X_FORWARDED_PROTO,https`


