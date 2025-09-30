# Architecture & Patterns (MVT + Services)

## Layout
- Базовая MVT-архитектура + тонкие views.
- Бизнес-логика — в **services** (`printing/services.py`) и **domain**-слое; views/serializers минимальны.
- Разделять `apps/` по доменам: `accounts`, `printing`, `common`.

## Data Access
- ORM только в репозиториях/сервисах; избегать сырого SQL без необходимости.
- Все тяжёлые выборки — с `select_related/prefetch_related`; агрегаты — кэшировать.

## Background
- Watcher-демон как отдельный процесс/сервис (см. Docker Compose). Идемпотентные операции, ретраи по ошибкам, понятные логи.

## Public API Stability
- Изменения контрактов — через депрекейшн-метки и совместимость в течение N минорных релизов (зафиксировать в CHANGELOG).

## Docs
- `docs/` с диаграммами (Mermaid/PlantUML). Для REST — OpenAPI через DRF-пакеты (по мере надобности).
