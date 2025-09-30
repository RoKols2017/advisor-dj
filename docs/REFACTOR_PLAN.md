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

Осталось:
- Подготовить и задействовать `.env.prod` (DEBUG=0, длинный SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS).
- Перевести прод-профиль на `DJANGO_SETTINGS_MODULE=config.settings.production` (в compose prod-оверлее).
- Включить в проде HTTPS-харденинг: `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS/INCLUDE_SUBDOMAINS/PRELOAD`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`.
- Убедиться, что все секреты и токены только через ENV; актуализировать `.env.example`.
- Логирование для прод: уровни INFO/ERROR, запись в файл/STDOUT, ротация (logrotate на хосте).
- Прогнать `python manage.py check --deploy` в прод-профиле до отсутствия предупреждений.

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

Осталось:
- Дочистить перенос бизнес-логики из `views` в `services` (аккуратные транзакции).
- Добавить сервисы для `accounts` и покрыть их тестами.
- Финальный проход по N+1 (вьюхи/таблицы) с `select_related/prefetch_related`.
- Добавить недостающие индексы по частым фильтрам/поиску и FK.
- Довести инвалидацию кэша агрегатов для всех затрагиваемых моделей; ввести TTL и базовые метрики (через логирование).
- Watcher: зафиксировать политику ретраев (максимум попыток, backoff, дедлайн) и оформление карантина (причина, хеш/дата, id).
- Разнести логи демона в отдельный handler/файл, согласовать уровни.

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

Осталось:
- Довести общее покрытие до ≥ 80% и вернуть порог в CI до 80.
- Интеграционные тесты для `printing/print_events_watcher.py` (успех, ретраи, карантин).
- Тесты для `accounts/backends.py` (Windows backend), базовые и негативные кейсы.
- Расширить интеграционные тесты на PostgreSQL: транзакции, уникальность/CI-lookups, индексы.
- Добить типизацию mypy в проблемных местах (`printing/services.py`, `accounts/services.py`) без неоправданных `ignore`.
- (Опционально) минимальные e2e: логин → импорт через UI → проверка результата.
- Публиковать HTML-репорт покрытия как артефакт CI.

## Этап 4: DevOps/CI/CD (1–2 недели)

Цель: предсказуемый деплой.

Задачи:
- Dockerfile для web (gunicorn) и watcher; `docker-compose.yml` (web+watcher+db).
- Healthchecks, volumes (`logs/`, `data/`, `pgdata/`).
- GitHub Actions: линтеры/типы/тесты/coverage, сборка Docker, smoke-тест runserver, `pip-audit`.

DoD:
- `docker compose up` поднимает весь стек; CI зелёный.

Осталось:
- Удалить устаревший ключ `version` в `docker-compose.yml` (устраняет warning).
- Добавить `docker-compose.prod.yml` (reverse proxy Nginx/Traefik с TLS, редирект 80→443, HSTS).
- Для prod-профиля переключить `DJANGO_SETTINGS_MODULE` на `config.settings.production` и использовать `.env.prod`.
- Подключить источник импорта: RO bind-монт Windows-шары `/mnt/printshare:/app/data/watch:ro` или SFTP pull.
- Настроить бэкапы БД (cron + `pg_dump`, retention) и ротацию логов.
- В CI добавить job деплоя по тегу `v*.*.*`: `docker login ghcr`, `build-push`, на прод-сервере `compose pull/up`, `migrate`, `collectstatic`, smoke.
- Версионирование тегами образов (`latest-*`, `vX.Y.Z-*`); (опц.) SBOM/подпись (`syft`, `cosign`).
- Мониторинг/алерты: health, 5xx/Traceback, место на диске; (опц.) metrics exporters.
- Make-цели для прод: `up-prod`, `migrate-prod`, `smoke-prod`, `logs-prod`, `down-prod`.
- Обновить `docs/DEPLOY_PLAN.md`, добавить `docs/RUNBOOK.md` и зафиксировать чек-лист прод-валидации.

