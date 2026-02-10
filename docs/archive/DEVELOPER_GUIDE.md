---
title: "Developer Guide"
type: archive
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Developer Guide

## Overview
This project is a Django-based print monitoring system with support for Active Directory user import and print event tracking. It includes:
- Web interface (Django)
- Print event import (JSON)
- AD user import (CSV)
- Background watcher daemon for automatic file processing
- Centralized logging

## Project Structure
```
accounts/         # User models, authentication
printing/         # Print event models, importers, watcher daemon
config/           # Django settings and logging config
static/, templates/  # Static files and HTML templates
docs/             # Documentation
manage.py         # Django management script
requirements.txt  # Python dependencies
```

## Key Components
- **Django web app**: User interface, admin, statistics, import/export
- **Print events watcher**: Standalone daemon, monitors a directory for new files (JSON/CSV), imports data into Django
- **Centralized logging**: All logs go to `logs/`, file names are configurable via env

## Environment Variables
- `PRINT_EVENTS_WATCH_DIR` — Directory to watch for new files (JSON/CSV)
- `PRINT_EVENTS_PROCESSED_DIR` — Directory to move processed files
- `LOG_FILE_NAME` — Log file name (default: `project.log`, watcher uses `print_events_watcher.log`)
- `LOG_TO_FILE`, `LOG_TO_CONSOLE` — Enable/disable file/console logging

## Importing Data
- **Print events**: Drop JSON files into the watch directory. The watcher will import and move them.
- **AD users**: Drop CSV files (see format in README) into the watch directory. The watcher will import and move them.

## Running Locally
- Activate virtualenv: `source .venv/bin/activate` or `.\.venv\Scripts\activate`
- Run Django: `python manage.py runserver`
- Run watcher: `python -m printing.print_events_watcher`

## Logging
- All logs are written to `logs/`.
- Log file names and handlers are controlled via env and `config/logging.py`.

---

## Running with Docker Compose (Recommended for Production)

**Best practice:** run Django and the watcher as separate services in one compose project, sharing the same code, database, and file volumes.

### Example `docker-compose.yml`
```yaml
version: '3.8'
services:
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - logs:/app/logs
      - data:/app/data
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - db
  watcher:
    build: .
    command: python -m printing.print_events_watcher
    volumes:
      - .:/app
      - logs:/app/logs
      - data:/app/data
    env_file:
      - .env
    depends_on:
      - web
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: advisor
      POSTGRES_USER: advisor
      POSTGRES_PASSWORD: advisor
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  logs:
  data:
  pgdata:
```

### How it works
- Both `web` and `watcher` containers share the same code and logs.
- The watcher monitors the shared data directory for new files and imports them into the same database as Django.
- Logs from both services go to the `logs/` volume, but to different files (see `LOG_FILE_NAME`).

### To start:
```sh
docker-compose up --build
```

---

## Development Tips
- Use `.env` to configure all paths and logging.
- For local testing, you can run both Django and the watcher in separate terminals.
- For production, always use separate processes/containers for Django and the watcher.
- All import errors and results are logged; check logs for troubleshooting.

---

## Useful Commands
- `python manage.py createsuperuser` — create admin user
- `python manage.py migrate` — apply migrations
- `python manage.py collectstatic` — collect static files for production

---

## Contacts
For questions and support, contact the project maintainer. 
