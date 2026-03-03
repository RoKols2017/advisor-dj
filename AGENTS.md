# AGENTS.md

> Project map for AI agents. Keep this file up-to-date as the project evolves.

## Project Overview
Print Advisor is a Django application for importing and analyzing print activity data. The system includes a web app and a watcher daemon that processes incoming JSON/CSV files into persistent records.

## Tech Stack
- **Language:** Python 3.13
- **Framework:** Django 5.2
- **Database:** PostgreSQL 15 (primary), SQLite (local/dev scenarios)
- **ORM:** Django ORM

## Project Structure
```text
advisor-dj/
|- accounts/                 # Authentication, user-related domain logic
|- printing/                 # Core print domain: models, views, services, watcher
|- config/                   # Django project config (settings, urls, wsgi/asgi)
|- templates/                # Django template files
|- static/                   # Static assets served by Django/Nginx
|- tests/                    # Unit/integration/e2e test suites
|- docs/                     # Project documentation and operational guides
|- scripts/                  # Automation scripts (smoke checks, helpers)
|- infrastructure/           # Deployment/systemd and infra-related assets
|- data/                     # Watch/processed/quarantine file directories
|- docker-compose.yml        # Main local compose stack (web, watcher, db)
|- docker-compose.prod.yml   # Production compose stack
|- docker-compose.proxy.yml  # Nginx reverse-proxy compose stack
|- Dockerfile                # Web image definition
|- Dockerfile.watcher        # Watcher image definition
|- manage.py                 # Django management entrypoint
|- requirements.txt          # Python dependencies
|- pyproject.toml            # Ruff/Black/mypy/coverage configuration
|- pytest.ini                # pytest configuration and coverage gate
|- Makefile                  # Common operational targets
`- .ai-factory/              # AI Factory context files
```

## Key Entry Points
| File | Purpose |
|------|---------|
| `manage.py` | Primary Django CLI entrypoint for runserver/migrate/admin tasks |
| `config/settings/` | Environment-specific Django settings |
| `config/urls.py` | Root URL routing for the web application |
| `printing/services.py` | Core business logic layer used by views/import flows |
| `printing/print_events_watcher.py` | Daemon entrypoint for filesystem ingestion |
| `docker-compose.yml` | Multi-service local runtime definition |

## Documentation
| Document | Path | Description |
|----------|------|-------------|
| README | `README.md` | Project landing page |
| Getting Started | `docs/getting-started.md` | Install, run, first import |
| Configuration | `docs/configuration.md` | Environment variables and profiles |
| Architecture | `docs/architecture.md` | Structure and data flow |
| Deployment | `docs/deployment.md` | Docker and production rollout |
| Operations | `docs/operations.md` | Runbook and watcher operations |
| Testing | `docs/testing.md` | Tests, coverage, smoke checks |
| Security | `docs/security.md` | HTTPS and security settings |
| Troubleshooting | `docs/troubleshooting.md` | Common failures and fixes |

## AI Context Files
| File | Purpose |
|------|---------|
| `AGENTS.md` | This file — project structure map |
| `.ai-factory/DESCRIPTION.md` | Project specification and detected stack |
| `.ai-factory/ARCHITECTURE.md` | Architecture decisions and implementation guidelines |
| `.ai-factory.json` | Installed AI Factory skills and local flags |
