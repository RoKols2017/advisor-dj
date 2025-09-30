# Documentation Rules (Print Advisor)

## Philosophy
- Документация — **равноправный артефакт** проекта. Она должна быть актуальна, проверяема и структурирована.
- README служит витриной: статус, технологии, быстрый старт, тесты, деплой, навигация по docs.

## Structure
- `README.md`: статус, стек, быстрый старт, команды, CI/CD, структура проекта, документация, поддержка.
- `docs/`:
  - `STATUS.md` — статус и прогресс
  - `DEV_PLAN.md` — план разработки
  - `RUNBOOK.md` — эксплуатация
  - `DE_SCOPED.md` — отложенные функции
  - `reference/` — модели, API, frontend-компоненты
  - `how-to/` — setup, docker-deployment, production
  - `concepts/` — архитектура, дизайн-решения

## Conventions
- Каждый документ начинается с мета-блока:
  ```yaml
  ---
  title: "<Название>"
  type: project|guide|reference
  status: draft|approved
  last_verified: "YYYY-MM-DD"
  verified_against_commit: "<hash|branch>"
  owner: "@<nick>"
  ---
  ```

- README содержит бейджи (CI, coverage, status).
- В `docs/` допускаются Mermaid/PlantUML диаграммы.

## Maintenance
- При каждом релизе обновлять даты и статус в README и STATUS.md.
- В PR с изменением логики/архитектуры — обновлять соответствующие docs/*.
- Автотесты CI должны включать проверку валидности ссылок в документации.

## Tools
- Рекомендуется `mkdocs` или `Sphinx` для публикации.
- Для API — автогенерация схемы DRF → ReDoc/Swagger.
- Для моделей — autogen схемы через `django-extensions graph_models`.
