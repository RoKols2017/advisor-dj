---
title: "Refactor Plan (Print Advisor)"
type: project
status: draft
last_verified: "2025-09-29"
verified_against_commit: "latest"
owner: "@rom"
---

## Этап 1: Безопасность и конфиги (1–2 недели) — выполнено

Цель: безрисковый продакшн-конфиг.

Задачи:
- Разделить `config/settings/` на `base.py`, `development.py`, `production.py`, `test.py`.
- Вынести `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` в ENV (`python-dotenv` для dev).
- Prod: WhiteNoise, `SECURE_*`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`.
- Ввести `.env.example` и шаблон `.env`.

Команды проверки:
```bash
python manage.py check --deploy
```

DoD:
- Разделение настроек по окружениям — выполнено
- WhiteNoise и security headers в prod — выполнено
- `.env.example` добавлен — выполнено
- `check --deploy` — будет выполнен при наличии prod-окружения

## Этап 2: Архитектура и производительность (2–3 недели) — выполнено

Цель: корректная доменная логика и быстрые запросы.

Задачи:
- Вынести бизнес-правила импорта в сервисы; исправить lookups — выполнено (`printing/services.py`, `accounts/services.py`).
- Оптимизировать ORM: `select_related`/`prefetch_related` во вьюхах — выполнено.
- Кэширование агрегатов (Django cache) + инвалидация — выполнено.
- Watcher: quarantine директория и backoff — выполнено.
- Unit-тесты для сервисов — выполнено (`printing/tests/test_services.py`).

DoD:
- Импорт устойчив (дедупликация по `job_id`), агрегации кешируются и инвалидируются; нет заметных N+1.
- Все тесты проходят: `pytest -q` → 4 passed.

## Этап 3: Тесты и качество (2–3 недели) — выполнено

Цель: стабильный пайплайн качества.

Задачи:
- Подключить `pytest`, `pytest-django`, `factory_boy` — выполнено.
- Настроить `ruff`, `black`, `mypy --strict` — выполнено.
- Разделить tests: unit/integration; добавить фикстуры БД и фабрики — выполнено.
- Добавить тесты для всех основных модулей — выполнено.

DoD:
- Coverage ≥ 70%; линтеры и типизация зелёные — выполнено (78% coverage).
- 51 тест проходят (100% success rate) — выполнено.

## Этап 4: DevOps/CI/CD (1–2 недели)

Цель: предсказуемый деплой.

Задачи:
- Dockerfile для web (gunicorn) и watcher; `docker-compose.yml` (web+watcher+db).
- Healthchecks, volumes (`logs/`, `data/`, `pgdata/`).
- GitHub Actions: линтеры/типы/тесты/coverage, сборка Docker, smoke-тест runserver, `pip-audit`.

DoD:
- `docker compose up` поднимает весь стек; CI зелёный.

