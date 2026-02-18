---
title: "API Endpoints"
type: reference
status: draft
last_verified: "2026-02-18"
verified_against_commit: "latest"
owner: "@rom"
---

# API Endpoints

- Приложение использует серверный рендеринг Django (не DRF API).
- OpenAPI: `docs/reference/openapi.yaml` (пока не реализовано)
- Swagger UI / ReDoc: пока не подключены

## HTTP endpoints (актуальные маршруты)

- `GET /` — dashboard (`printing.dashboard`)
- `GET /events/` — список событий печати с фильтрами (может редиректить на URL с дефолтными датами)
- `GET /statistics/` — статистика по печати
- `GET /tree/` — иерархическое дерево событий
- `GET/POST /import/users/` — импорт пользователей из CSV
- `GET/POST /import/print-events/` — импорт событий печати из JSON
- `GET /user-info/` — карточка текущего пользователя
- `GET /health/` — health-check приложения
- `GET/POST /accounts/login/` — вход
- `POST /accounts/logout/` — выход
- `GET /admin/` — Django admin

## Security for import endpoints

- Для `POST /import/users/` и `POST /import/print-events/` обязателен токен импорта.
- Передача токена: заголовок `X-Import-Token`.
- Для HTML-форм также допускается поле `import_token` в body.
- При отсутствии/невалидном токене сервер возвращает `403 Forbidden`.
