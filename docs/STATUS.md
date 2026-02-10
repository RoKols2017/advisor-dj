---
title: "Project Status"
type: project
status: draft
last_verified: "2026-02-10"
verified_against_commit: "latest"
owner: "@rom"
---

# Status

- Current state:
  - Stage 1 (Security & Settings) — completed (prod‑профиль, `.env.prod.template`, security включены).
  - Stage 2 (Architecture & Performance) — выполнено по плану; остались доводки N+1/индексов и ретраев/карантина (задокументировано в рефакторинг‑плане).
  - Stage 3 (Tests & Code Quality) — 51 тест в каталоге `tests` проходят локально; порог покрытия в CI настроен на ≥ 80%.
  - Stage 4 (DevOps/CI/CD) — локальный Docker стек (web+watcher+db) green; CI собирает и тестирует; осталось prod‑overlay, деплой‑job и мониторинг.
- Quality metrics:
  - Test coverage: целевой порог 80% в CI (актуальное значение смотрите в CI/Codecov)
  - Tests: 51 tests passing (100% success rate)
  - Static analysis: ruff, black, mypy — configured
  - CI/CD: Lint/Test/Coverage + Docker build + smoke
- Risks:
  - Отсутствуют DRF/OpenAPI — medium
  - Прод‑оверлей (reverse proxy/TLS) в работе — medium
- Bugs:
  - Нет известных

