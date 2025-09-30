# Cursor / Ubuntu Setup

## Dev Workflow
- Создать venv (Python 3.13), установить зависимости из `requirements.txt`.
- В Cursor включить форматеры: `black`, линтер `ruff`, `mypy`.
- Запуск: `python manage.py runserver 0.0.0.0:8000`, watcher — в отдельном терминале или Docker.

## Commands (Makefile рекомендован)
- `make setup` — установка dev-зависимостей
- `make lint` — ruff + black --check + mypy
- `make test` — pytest
- `make run` — локальный сервер
- `make compose-up` — docker-compose up --build
