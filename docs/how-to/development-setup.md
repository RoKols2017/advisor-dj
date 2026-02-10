---
title: "Development Setup"
type: guide
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Development Setup

## Prerequisites

- Python 3.12+ (в CI используется 3.13)
- pip
- Git

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment

```bash
cp .env.example .env
```

Если `.env.example` отсутствует, используйте `docs/ENV.md` как источник переменных.

## Database and run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Tests and quality checks

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest -q tests
ruff check .
black --check .
mypy .
```

## Notes

- Основной URL: `http://127.0.0.1:8000`
- Логин: `/accounts/login/`
- Health: `/health/`
