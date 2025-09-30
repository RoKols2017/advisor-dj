---
title: "Print Advisor"
type: project
status: draft
last_verified: "2025-09-29"
verified_against_commit: "latest"
owner: "@rom"
---

# Print Advisor 🖨️

[![CI](https://img.shields.io/badge/ci-passing-brightgreen)](#) [![Coverage](https://img.shields.io/badge/coverage-78%25-brightgreen)](#) [![Status](https://img.shields.io/badge/status-active-brightgreen)](#)

## 📊 Статус проекта

- Этап: draft (MVP)
- Основные риски/баги: см. `docs/STATUS.md`

## 🛠️ Технологии

- Backend: Python 3.13, Django 5.x
- DB: SQLite (локально), PostgreSQL (prod)
- UI: Django Templates, Bootstrap 5
- Дополнительно: django-tables2, django-filter, django-import-export

## 🚀 Быстрый старт (WSL/Ubuntu)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env || true
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Откройте `http://127.0.0.1:8000` (админка: `/admin`).

## 🏗️ Staging / Production

- Docker Compose: см. `docs/how-to/docker-deployment.md`
- Production checklist: см. `docs/how-to/production-deployment.md`

## 🧪 Тестирование

```bash
# Быстрые тесты
pytest -q

# С покрытием кода
pytest --cov=. --cov-report=term-missing --cov-fail-under=80

# Только unit-тесты
pytest tests/unit/ -q

# Интеграционные тесты
pytest tests/integration/ -q

# Все тесты с маркерами
pytest -m "not slow" -q
```

**Пороги покрытия:**
- Общий проект: ≥ 80% (текущее: 78% ✅)
- Изменённые файлы: ≥ 85%
- Всего тестов: 51 (100% проходят)

## 🔄 CI/CD

- CI: линтеры, тесты, сборка статики, сборка документации (`mkdocs build`)
- Публикация артефактов: OpenAPI, диаграмма моделей

## 📁 Структура проекта

```
accounts/   printing/   config/   templates/   static/   docs/   manage.py
```

## 📚 Документация

- Статус и прогресс: `docs/STATUS.md`
- План разработки: `docs/DEV_PLAN.md`
- Руководство эксплуатации: `docs/RUNBOOK.md`
- Архитектурные заметки: `docs/concepts/`
- Справочник: `docs/reference/` (API, модели, UI)
- How-to: `docs/how-to/`
- Архив устаревших документов: `docs/archive/`

## 📞 Поддержка

- Создайте Issue с описанием проблемы и приложите логи из `logs/`.


