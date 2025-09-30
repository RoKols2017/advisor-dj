# Web & Management Commands (Django/DRF)

## Django Views
- CBV предпочтительны для CRUD и списков (django-tables2/filters — ок).
- Views тонкие: вью — маршрутизация/валидация, бизнес-логика — в сервисах.

## DRF
- Серилизаторы валидируют входные данные. ViewSets тонкие.
- Глобальные обработчики ошибок → унифицированные ответы (при необходимости).

## Security
- CSRF включён для HTML-форм.
- Импорт событий: `POST /import/print-events/` — CSRF для UI, либо заголовок `X-Import-Token` (значение из ENV).

## Management Commands
- Любая фонова задача (разовая) — менеджмент-команда с `--help`, типами и тестом.
