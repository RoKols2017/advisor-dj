---
title: "Audit Report (Print Advisor)"
type: project
status: draft
last_verified: "2025-09-29"
verified_against_commit: "latest"
owner: "@rom"
---

## Executive summary

1) В прод-настройках потенциальная утечка секретов/уязвимости: `SECRET_KEY` в репо, `DEBUG=True`, пустые `ALLOWED_HOSTS`, нет `SECURE_*`/WhiteNoise.
2) Настройки не разделены по окружениям; нет чтения ENV (БД, флаги auth, логирование) → сложный прод-деплой/безопасность.
3) Watcher и импортеры без строгой идемпотентности и валидации входа; возможны дубли и некорректные `get_or_create` фильтры.

## Матрица соответствия правилам

| Область | Статус | Детали | Ссылка |
| --- | --- | --- | --- |
| Безопасность (SECRET_KEY/DEBUG/HOSTS) | critical | Хардкод ключа, DEBUG включён, `ALLOWED_HOSTS=[]` | `config/settings.py:23-31` |
| Security headers/SECURE_* | high | Отсутствуют | `config/settings.py` |
| CSRF/XSS/Host header | medium | Базовые middleware есть, спец-настроек нет | `config/settings.py:52-60` |
| Настройки по окружениям | critical | Один файл settings, нет ENV | `config/settings.py` |
| База данных (prod=Postgres) | high | Только SQLite | `config/settings.py:86-91` |
| Static/WhiteNoise | high | Нет WhiteNoise | `config/settings.py:136-143` |
| Логирование/ротация | low | Ротация есть, фильтра чувств.данных нет | `config/logging.py` |
| Watcher: ретраи/идемп. | medium | Ретраи есть, идемп. частичная по `job_id` | `printing/print_events_watcher.py`, `printing/importers.py` |
| Импорт: ORM фильтры | high | Некорректные `get_or_create` с `__iexact` в lookup | `printing/importers.py:36-41, 120-126, 129-136` |
| DRF/API | medium | DRF не подключён, схема/пагинация нет | `INSTALLED_APPS` |
| Качество кода (ruff/black/mypy/pytest) | medium | Конфигов нет | repo |
| CI/CD | medium | Скриптов/конфигов CI нет | repo |
| Docker/Compose | medium | Нет манифестов | repo |
| Windows Auth флаг | medium | Бэкенд есть, флага `ENABLE_WINDOWS_AUTH` нет | `accounts/backends.py`, `config/settings.py` |

## Найденные проблемы (с примерами)

- critical: Хардкод секретов/DEBUG/hosts
  - Почему: нарушает безопасность прод.
  - Где: `config/settings.py:23-31`.
  - Исправить: вынести в ENV, разделить settings.

- high: База данных только SQLite
  - Где: `config/settings.py:86-91`.
  - Исправить: Postgres через `DATABASE_URL`/ENV в production.

- high: Static/WhiteNoise отсутствует
  - Где: `config/settings.py:136-143`.
  - Исправить: WhiteNoise в prod + `collectstatic`.

- high: Неверные фильтры в `get_or_create`
  - Где: `printing/importers.py:36-41` и далее: используется `get_or_create(code__iexact=...)` — lookup нельзя в kwargs ключах; это приведёт к созданию дублей.
  - Исправить: `Department.objects.filter(code__iexact=dept_code).first() or Department.objects.create(...)` или нормализовать код и использовать `code=normalized`.

- medium: Частичная идемпотентность импорта
  - Где: `printing/importers.py:96-99` только по `job_id`; нет уникального индекса/валидации.
  - Исправить: уникальный индекс по `job_id`, валидация входа, quarantine каталог.

- medium: Windows Auth без флага
  - Где: `accounts/backends.py`; в `INSTALLED_APPS` нет доп. зависимостей, но импорт `pywin32` в Linux упадёт при активации.
  - Исправить: подключать по `ENABLE_WINDOWS_AUTH=1` и безопасные импорты с fallback.

- medium: Отсутствуют DRF/схема OpenAPI
  - Исправить: добавить DRF, `drf-spectacular`, пагинацию и фильтрацию.

- low: Нет фильтров чувствительных данных в логах
  - Исправить: `FILTERS` в LOGGING и mask для секретов.

## Быстрые победы (quick wins)

- Вынести `SECRET_KEY/DEBUG/ALLOWED_HOSTS/DATABASE_URL` в ENV; добавить `.env.example`.
- Разделить settings (base/dev/prod/test). В prod: WhiteNoise, `SECURE_*`, `CSRF_COOKIE_SECURE`.
- Исправить `get_or_create` в импортёрах; добавить уникальный индекс на `PrintEvent.job_id`.
- Добавить DRF + `drf-spectacular` и генерацию `docs/reference/openapi.yaml`.
- Добавить GitHub Actions: ruff/black/mypy/pytest + `pip-audit`.

