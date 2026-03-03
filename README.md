# Print Advisor

> Django-приложение для импорта, мониторинга и анализа печати из JSON/CSV источников.

[![CI](https://img.shields.io/badge/ci-passing-brightgreen)](#) [![Coverage](https://img.shields.io/badge/coverage-see%20CI-blue)](#) [![Status](https://img.shields.io/badge/status-active-brightgreen)](#)

Print Advisor объединяет веб-интерфейс для операторов и фоновый watcher, который автоматически подхватывает файлы, загружает события печати в БД и раскладывает обработанные/ошибочные данные по отдельным каталогам.

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env || true
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Откройте `http://127.0.0.1:8000` (админка: `http://127.0.0.1:8000/admin`).

## Ключевые возможности

- Автоматический импорт печатных событий и пользователей из `JSON`/`CSV`
- Разделение файлов на `watch`, `processed`, `quarantine` для устойчивой обработки
- Веб-дашборды и health endpoint для операционного контроля
- Запуск в Docker (`web`, `watcher`, `db`) с поддержкой reverse proxy

## Пример

```bash
# 1) Поднять стек
docker compose up --build -d

# 2) Применить миграции
docker compose exec web python manage.py migrate

# 3) Проверить health
curl http://localhost/health

# 4) Положить файл для watcher
cp ./tests/fixtures/events_valid.json ./data/watch/
docker compose logs watcher --tail=50
```

Если импорт успешен, файл переместится в `data/processed/`.

## Документация

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started.md) | Установка, запуск и первый импорт |
| [Configuration](docs/configuration.md) | Переменные окружения и профили |
| [Architecture](docs/architecture.md) | Структура проекта и поток данных |
| [Deployment](docs/deployment.md) | Docker/Production и запуск в ЛВС |
| [Operations](docs/operations.md) | Runbook, watcher и операционные задачи |
| [Testing](docs/testing.md) | Тесты, покрытие и smoke-проверки |
| [Troubleshooting](docs/troubleshooting.md) | Частые проблемы и быстрые фиксы |

Дополнительно:
- Подробный чеклист деплоя: `docs/DEPLOYMENT_CHECKLIST.md`
- Readiness для нового сервера: `docs/DEPLOYMENT_READINESS.md`
- Nginx/HTTPS детали: `docs/NGINX_REVERSE_PROXY_IMPLEMENTATION.md`, `docs/WINDOWS_CA_CERTIFICATES.md`
- Статус проекта и риски: `docs/STATUS.md`

## Лицензия

Внутренний проект команды. Правила использования определяются владельцем репозитория.
