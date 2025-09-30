---
title: "Deploy Plan (Print Advisor)"
type: guide
status: completed
last_verified: "2025-09-30"
verified_against_commit: "latest"
owner: "@rom"
---

## 🐳 Docker Services

### Сервисы
- **web**: Django + gunicorn + WhiteNoise (порт 8000)
- **watcher**: python -m printing.print_events_watcher (демон)
- **db**: PostgreSQL 15 (порт 5432)

### Volumes
- `pgdata`: данные PostgreSQL
- `logs`: логи приложения
- `data`: файлы для обработки (watch/, processed/, quarantine/)

### Networks
- `advisor-network`: внутренняя сеть для сервисов

## 🚀 Quick Start

```bash
# Клонировать репозиторий
git clone <repository-url>
cd advisor-dj

# Настроить окружение
cp .env.example .env
# Отредактировать .env с вашими настройками

# Запустить стек
make up-build
# или
docker compose up --build -d

# Проверить статус
make status
# или
docker compose ps

# Запустить миграции
make migrate

# Проверить здоровье
make smoke
```

## 🔧 Makefile Commands

```bash
make help          # Показать все команды
make build         # Собрать образы
make up            # Запустить сервисы
make up-build      # Запустить с пересборкой
make down          # Остановить сервисы
make logs          # Показать логи всех сервисов
make logs-web      # Логи web-сервиса
make logs-watcher  # Логи watcher-сервиса
make logs-db       # Логи базы данных
make smoke         # Запустить smoke-тесты
make migrate       # Выполнить миграции
make collectstatic # Собрать статические файлы
make shell         # Django shell
make test          # Запустить тесты
make lint          # Проверка кода
make clean         # Очистка контейнеров и volumes
make restart       # Перезапуск сервисов
make status        # Статус сервисов
make health        # Проверка здоровья
```

## 🏥 Health Checks

### Web Service
- **URL**: `http://localhost:8000/health/`
- **Check**: HTTP 200 с JSON статусом
- **Interval**: 30s, timeout: 10s, retries: 3

### Watcher Service
- **Check**: процесс `printing.print_events_watcher` запущен
- **Interval**: 30s, timeout: 10s, retries: 3

### Database Service
- **Check**: `pg_isready -U advisor -d advisor`
- **Interval**: 10s, timeout: 5s, retries: 5

## 🔒 Environment Variables

### Required
```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@db:5432/dbname
POSTGRES_PASSWORD=secure-password
```

### Optional
```env
DEBUG=0
ALLOWED_HOSTS=localhost,example.com
LOG_TO_FILE=1
LOG_TO_CONSOLE=0
IMPORT_TOKEN=your-import-token
ENABLE_WINDOWS_AUTH=0
```

## 📊 Monitoring

### Logs
```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f web
docker compose logs -f watcher
docker compose logs -f db

# Последние 100 строк
docker compose logs --tail=100 web
```

### Health Status
```bash
# Проверка здоровья
curl http://localhost:8000/health/

# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats
```

## 🔄 CI/CD Pipeline

### GitHub Actions
1. **Lint & Type Check**: ruff, black, mypy
2. **Tests**: pytest с покрытием (SQLite + PostgreSQL)
3. **Security**: pip-audit проверка зависимостей
4. **Build**: Docker образы (web, watcher)
5. **Smoke Tests**: полный стек + health checks

### Artifacts
- Docker images: `ghcr.io/owner/repo:tag-web`, `ghcr.io/owner/repo:tag-watcher`
- Coverage reports: XML + HTML
- Security reports: pip-audit JSON

## 🚨 Troubleshooting

### Common Issues

#### Services not starting
```bash
# Проверить логи
docker compose logs

# Проверить конфигурацию
docker compose config

# Пересобрать образы
docker compose build --no-cache
```

#### Database connection issues
```bash
# Проверить статус БД
docker compose exec db pg_isready -U advisor

# Проверить переменные окружения
docker compose exec web env | grep DATABASE
```

#### Health check failures
```bash
# Проверить health endpoint
curl -v http://localhost:8000/health/

# Проверить процессы в контейнерах
docker compose exec web ps aux
docker compose exec watcher ps aux
```

### Recovery Commands
```bash
# Полная перезагрузка
make clean
make up-build

# Только перезапуск сервиса
docker compose restart web

# Проверка после изменений
make smoke
```