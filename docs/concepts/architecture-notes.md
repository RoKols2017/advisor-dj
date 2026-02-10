---
title: "Architecture Notes"
type: project
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Architecture Notes

## High-level overview

- Приложение построено на Django (MVT) с двумя доменными приложениями: `accounts` и `printing`.
- Веб-слой: Django templates + class-based views.
- Бизнес-слой: сервисные функции в `accounts/services.py` и `printing/services.py`.
- Фоновая обработка: watcher (`printing/print_events_watcher.py`) для импорта CSV/JSON.

## Design decisions

- Настройки разделены по окружениям (`base`, `development`, `test`, `production`, `docker`).
- Импорт данных отделен от views и используется из watcher/ручных импортов.
- Кэширование агрегатов вынесено в сервисы статистики.
- Docker-композиция поддерживает основной стек и отдельный reverse proxy слой.

## Known trade-offs

- Часть сложной агрегации дерева реализована на уровне Python-кода во view.
- Исторические документы в `docs/` содержат аналитические срезы, которые могут отличаться от текущего состояния кода.
