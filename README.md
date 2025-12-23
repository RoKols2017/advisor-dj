---
title: "Print Advisor"
type: project
status: draft
last_verified: "2025-12-23"
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
- DB: SQLite (локально), PostgreSQL 15 (production)
- UI: Django Templates, Bootstrap 5
- Дополнительно: django-tables2, django-filter, django-import-export
- Контейнеризация: Docker, Docker Compose
- Мониторинг: Автоматический watcher для обработки файлов (JSON/CSV)

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

### Архитектура

Приложение состоит из трех сервисов:
- **web**: Django веб-приложение (порт 8001 по умолчанию)
- **watcher**: Демон мониторинга каталога для автоматического импорта данных
- **db**: PostgreSQL 15 база данных (порт 5432)

Все сервисы имеют политику автоматического перезапуска (`restart: unless-stopped`).

### Quick Start with Docker
```bash
# Клонировать и настроить
git clone git@github.com:RoKols2017/advisor-dj.git
cd advisor-dj

# Сгенерировать .env файл со всеми необходимыми ключами
./scripts/generate_env.sh

# Или интерактивный режим для настройки параметров
# ./scripts/generate_env.sh --interactive

# Создать каталоги для данных
mkdir -p data/{watch,processed,quarantine}
sudo chmod 777 data/{watch,processed,quarantine}

# Запустить весь стек
make up-build
# или
docker compose up --build -d

# Выполнить миграции
docker compose exec web python manage.py migrate

# Создать суперпользователя
docker compose exec web python manage.py createsuperuser

# Проверить статус
make status
make smoke
```

### Автозапуск при старте системы

Для автоматического запуска контейнеров при перезагрузке сервера:

```bash
sudo cp advisor-dj.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable advisor-dj.service
sudo systemctl start advisor-dj.service
```

### Автоматический импорт данных

Watcher автоматически отслеживает каталог `data/watch/` и обрабатывает:
- **JSON-файлы** → импорт событий печати
- **CSV-файлы** → импорт пользователей

Обработанные файлы перемещаются в `data/processed/`, файлы с ошибками — в `data/quarantine/`.

### Production Deployment

- **Полная документация**: `docs/DEPLOYMENT_READINESS.md` и `docs/DEPLOYMENT_CHECKLIST.md`
- **Docker Compose**: `docs/DEPLOY_PLAN.md`
- **Health Checks**: автоматические проверки всех сервисов
- **Monitoring**: логи, метрики, smoke-тесты
- **CI/CD**: GitHub Actions с Docker образами
- **Развертывание в ЛВС без интернета**: см. `docs/DEPLOYMENT_CHECKLIST.md`

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
advisor-dj/
├── accounts/          # Управление пользователями и аутентификация
├── printing/          # Основное приложение (модели, views, watcher)
├── config/            # Настройки Django (settings, urls, logging)
├── templates/         # HTML шаблоны
├── static/            # Статические файлы (CSS, JS)
├── data/              # Каталоги для обработки файлов (watch, processed, quarantine)
├── docs/              # Документация
├── scripts/           # Вспомогательные скрипты (smoke tests, monitoring)
├── docker-compose.yml # Конфигурация Docker Compose
├── Dockerfile         # Образ для web-сервиса
├── Dockerfile.watcher # Образ для watcher-сервиса
├── advisor-dj.service # Systemd unit для автозапуска
└── manage.py          # Django management скрипт
```

## 📚 Документация

### Основная документация

- **Развертывание**: 
  - [docs/DEPLOYMENT_READINESS.md](docs/DEPLOYMENT_READINESS.md) - готовность и чеклист для нового сервера
  - [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) - подробный чеклист для ЛВС без интернета
  - [docs/DEPLOY_PLAN.md](docs/DEPLOY_PLAN.md) - общий план деплоя
  - [docs/DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md) - руководство по деплою
- **Watcher и файлы**: [docs/FILE_WATCHER_SETUP.md](docs/FILE_WATCHER_SETUP.md) - настройка watcher и прав доступа
- **Эксплуатация**: [docs/RUNBOOK.md](docs/RUNBOOK.md) - операционные задачи
- **Статус проекта**: [docs/STATUS.md](docs/STATUS.md) - текущий статус и риски
- **Переменные окружения**: [docs/ENV.md](docs/ENV.md) - описание переменных окружения

### Дополнительная документация

- План рефакторинга: [docs/REFACTOR_PLAN.md](docs/REFACTOR_PLAN.md)
- Критический анализ: [docs/CRITICAL_ANALYSIS.md](docs/CRITICAL_ANALYSIS.md)
- План разработки: [docs/DEV_PLAN.md](docs/DEV_PLAN.md)
- How-to гайды: [docs/how-to/](docs/how-to/) - Windows SMB шары, разработка, деплой
- Справочная информация: `docs/concepts/`, `docs/reference/`
- Архив: `docs/archive/`

## 📞 Поддержка

- Создайте Issue с описанием проблемы и приложите логи из `logs/`.


