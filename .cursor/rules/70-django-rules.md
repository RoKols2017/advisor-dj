# Django-Specific Rules

## Settings
- Разделять `config/settings/` на `base.py`, `development.py`, `production.py`, `test.py`.
- Все секреты/флаги — из ENV. `DEBUG=False` в проде, `ALLOWED_HOSTS` не пуст.

## Security
- Включить WhiteNoise или CDN для статики в продакшне.
- Заголовки безопасности (`SECURE_*`, HSTS) при `DEBUG=False`.
- `AUTHENTICATION_BACKENDS` подключать Windows-бэкенд условно через `ENABLE_WINDOWS_AUTH`.

## Templates/Static
- Bootstrap 5 — базовая тема; минимальный custom JS.
- Никакого inline HTML из внешних данных без экранирования.

## Logging
- Централизованный конфиг в `config/logging.py`; ротация файлов; разные файлы для web/watcher.
