# Testing, Linting, Tooling (Django)

## Testing
- Фреймворк: **pytest + pytest-django**. Покрытие ≥ 85% для изменённых файлов.
- Структура:
  - `tests/unit/` — функции, сервисы, утилиты
  - `tests/integration/` — ORM/DB, DRF API, watcher
  - `tests/e2e/` — по мере необходимости
- Использовать **fixtures**, `parametrize`, для нетривиальной логики — **hypothesis**.
- Любая найденная ошибка → сперва **регрессионный тест**, потом фикс.

## Static Analysis
- Команды по умолчанию:
  - `ruff check .`
  - `black --check .`
  - `mypy .`
  - `pytest -q`
- Безопасность: `pip-audit`/`safety` в CI.

## Security & Data
- Не логировать секреты. Конфиги через `.env` + переменные окружения.
- Веб: CSRF включён, ввод валидировать (формы/серилизаторы). Заголовок `X-Import-Token` для импорта событий.

## Performance
- Профилирование: `cProfile`, `django-silk` (dev only). Использовать `select_related/prefetch_related`, кэш для тяжёлых агрегатов.
