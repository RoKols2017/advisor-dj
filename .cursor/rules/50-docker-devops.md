# Docker & DevOps (Ubuntu + Cursor)

## Services
- **web**: Django + gunicorn
- **watcher**: `python -m printing.print_events_watcher`
- **db**: Postgres 15
- Общие volume'ы: `logs/`, `data/`, `pgdata/`

## Compose Hints
- Один `.env` для dev/prod, чувствительные значения — через секреты.
- Логи обоих сервисов — в `logs/` с разными файлами.
- Проверки прод-конфига: `python manage.py check --deploy`.

## ENV (минимум)
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DB_*` или `DATABASE_URL`
- `ENABLE_WINDOWS_AUTH` (0/1)
- `IMPORT_TOKEN`
- `LOG_DIR`, `LOG_TO_FILE`, `LOG_TO_CONSOLE`, `LOG_FILE_NAME`
