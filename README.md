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

## 🏗️ Docker / Production

### Quick Start with Docker
```bash
# Клонировать и настроить
git clone <repository-url>
cd advisor-dj
cp .env.example .env

# Запустить весь стек
make up-build
# или
docker compose up --build -d

# Проверить статус
make status
make smoke
```

### Production Deployment
- **Docker Compose**: полная документация в `docs/DEPLOY_PLAN.md`
- **Health Checks**: автоматические проверки всех сервисов
- **Monitoring**: логи, метрики, smoke-тесты
- **CI/CD**: GitHub Actions с Docker образами

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

### GitHub Actions Pipeline
1. **Lint & Type Check**: ruff, black, mypy
2. **Tests**: pytest с покрытием (SQLite + PostgreSQL) 
3. **Security**: pip-audit проверка зависимостей
4. **Docker Build**: образы web и watcher сервисов
5. **Smoke Tests**: полный стек + health checks

### Artifacts
- **Docker Images**: `ghcr.io/owner/repo:tag-web`, `ghcr.io/owner/repo:tag-watcher`
- **Coverage Reports**: XML + HTML
- **Security Reports**: pip-audit JSON

## 📁 Структура проекта

```
accounts/   printing/   config/   templates/   static/   docs/   manage.py
```

## 📚 Документация

- Статус проекта: [docs/STATUS.md](docs/STATUS.md)
- План рефакторинга: [docs/REFACTOR_PLAN.md](docs/REFACTOR_PLAN.md)
- План деплоя: [docs/DEPLOY_PLAN.md](docs/DEPLOY_PLAN.md)
- Runbook (эксплуатация): [docs/RUNBOOK.md](docs/RUNBOOK.md)
- Переменные окружения (ENV): [docs/ENV.md](docs/ENV.md)
- How-to: Windows SMB шары → watcher: [docs/how-to/windows-share.md](docs/how-to/windows-share.md)
- Дополнительно: [docs/DEV_PLAN.md](docs/DEV_PLAN.md), `docs/concepts/`, `docs/reference/`, `docs/how-to/`, `docs/archive/`

## 📞 Поддержка

- Создайте Issue с описанием проблемы и приложите логи из `logs/`.


