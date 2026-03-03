[← Configuration](configuration.md) · [Back to README](../README.md) · [Deployment →](deployment.md)

# Architecture

## Общая схема

Print Advisor - модульный монолит на Django с двумя основными доменами:
- `accounts` - аутентификация и пользовательские сущности
- `printing` - импорт, модели печати, обработка и отчеты

## Компоненты рантайма

| Компонент | Назначение |
|---|---|
| `web` | Django приложение и HTTP интерфейс |
| `watcher` | Фоновый обработчик файлов из watch-каталога |
| `db` | PostgreSQL 15 |
| `nginx` | Reverse proxy (опционально, для prod/LAN) |

## Поток данных импорта

1. Файл попадает в `data/watch/`
2. `watcher` обнаруживает `*.json` или `*.csv`
3. Сервисный слой в `printing/services.py` выполняет импорт
4. При успехе файл уходит в `data/processed/`
5. При ошибке файл уходит в `data/quarantine/`

## Структура проекта

```text
accounts/               # Пользователи и авторизация
printing/               # Бизнес-логика печати и watcher
config/                 # settings/urls/wsgi/asgi
templates/              # Django templates
static/                 # Статика
tests/                  # Unit/integration/e2e
docs/                   # Документация
scripts/                # Служебные скрипты
```

## Где смотреть детали

- Архитектурные решения: `.ai-factory/ARCHITECTURE.md`
- Карта проекта для агентов: `../AGENTS.md`

## See Also

- [Deployment](deployment.md) - как эта архитектура запускается в Docker
- [Operations](operations.md) - мониторинг и эксплуатация компонентов
- [Testing](testing.md) - как проверять корректность слоев
