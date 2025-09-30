# Watcher Daemon Rules

## Responsibilities
- Следит за директорией (`PRINT_EVENTS_WATCH_DIR`), обрабатывает JSON/CSV, переносит в `PRINT_EVENTS_PROCESSED_DIR`.
- Идемпотентность: повторная обработка файла не приводит к дублям (использовать хэши/идемпотентные ключи).
- Подробные, но безопасные логи (без данных пользователей/секретов).

## Failures
- Ретраи с бэкоффом, quarantine-папка для проблемных файлов.
- Метрики: количество обработанных/ошибок; время обработки.

## Packaging
- Отдельный entrypoint: `python -m printing.print_events_watcher`.
- Конфиг через ENV, тесты — интеграционные (с tmpdir).
