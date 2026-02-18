# AGENTS.md
Repository guide for agentic coding assistants working in `advisor-dj`.

## Project quick facts
- Stack: Python 3.13, Django 5.2, pytest, Ruff, Black, mypy, Docker Compose.
- Apps: `accounts/`, `printing/`, `config/`.
- Test settings: `DJANGO_SETTINGS_MODULE=config.settings.test`.

## Rule sources to honor
Cursor rules present in this repo:
- `.cursor/rules/00-core.md`
- `.cursor/rules/10-python-style.md`
- `.cursor/rules/15_env_files_policy.md`
- `.cursor/rules/20-testing-quality.md`
- `.cursor/rules/30-architecture.md`
- `.cursor/rules/40-web-and-cli.md`
- `.cursor/rules/50-docker-devops.md`
- `.cursor/rules/60-cursor-setup.md`
- `.cursor/rules/70-django-rules.md`
- `.cursor/rules/80-watcher-daemon.md`
- `.cursor/rules/90-guardrails-and-checklists.md`
- `.cursor/rules/95-documentation.md`
- `.cursor/rules/98_documentation.md`

Copilot instructions:
- `.github/copilot-instructions.md` not found.

## Setup, build, lint, test
Local setup:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
```

Docker setup and run:
```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
```

Make targets available now:
```bash
make build
make up
make up-build
make down
make logs
make test
make lint
make smoke
```

Note: `.cursor/rules/60-cursor-setup.md` mentions `make setup`, `make run`,
`make compose-up`; these targets do not exist in current `Makefile`.

Quality commands (local):
```bash
ruff check .
black --check .
mypy .
pytest -q
```

Docker quality commands:
```bash
make lint
make test
```

Auto-fix formatting:
```bash
ruff check . --fix
black .
```

Test subsets:
```bash
pytest tests/unit -q
pytest tests/integration -q
pytest tests/e2e -q
pytest -m "not slow" -q
```

## Running a single test (important)
Use these patterns:
```bash
# single file
pytest tests/unit/test_services.py -q

# single test function
pytest tests/unit/test_services.py::test_import_print_events_creates_records -q

# single class
pytest tests/integration/test_views.py::TestStatisticsView -q

# by keyword expression
pytest -k "import_print_events and not slow" -q

# same in Docker
docker compose exec web pytest tests/unit/test_services.py::test_import_print_events_creates_records -q
```

Coverage expectations:
- Global gate: `--cov-fail-under=80` (`pytest.ini`).
- Preferred confidence on changed files: >=85% (Cursor testing guidance).

## Code style guidelines
Formatting and imports:
- Black line length is 120.
- Ruff rules include `E,F,I,B,UP,C4,SIM,TCH`.
- Import order: stdlib -> third-party -> local.
- Avoid wildcard imports.

Typing:
- `mypy` strict mode is enabled.
- Add type hints for public and modified APIs.
- Avoid `Any`; if unavoidable, keep usage narrow and explicit.
- Prefer `dataclass`/`TypedDict` for structured payloads.

Naming:
- `snake_case` for functions/variables/modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for constants.
- Use explicit domain names; avoid unclear abbreviations.

Architecture and Django patterns:
- Keep views thin; place business logic in services.
- Follow current service-centric pattern (`printing/services.py`).
- Prefer CBVs for list/filter/CRUD flows.
- Optimize ORM with `select_related`, `prefetch_related`, DB aggregates.

Error handling and logging:
- Catch specific exceptions where possible.
- Do not silently swallow exceptions.
- At batch/import boundaries, log errors and continue when safe.
- Use `logging`, not `print`, in app/library code.
- Use `exc_info=True` for unexpected failures.
- Never log secrets/tokens/credentials.

Security and environment:
- Read config and secrets from environment variables.
- Do not edit `.env*` files without explicit user approval.
- Keep CSRF protections enabled for HTML form flows.
- Import API contract may rely on `X-Import-Token`.

Watcher daemon expectations:
- Entrypoint: `python -m printing.print_events_watcher`.
- Preserve idempotency, retries/backoff, and quarantine handling.
- Keep watcher logs operational and safe.

## Testing and delivery checklist
- For bug fixes, add/update a regression test first.
- Prefer unit tests; add integration tests for ORM/view/import behavior.
- Use markers correctly: `unit`, `integration`, `e2e`, `slow`.
- Keep tests deterministic; avoid hidden time/env coupling.
- Run `ruff`, `black --check`, `mypy`, `pytest -q` before finishing.

Documentation checklist:
- Update relevant files in `docs/` for behavior/config/deploy changes.
- Keep docs concise and reproducible on Ubuntu.
- Update `last_verified` where doc metadata requires it.
- Prefer relative repository paths in docs and PR notes.
- If rule text conflicts with code, follow code and note the mismatch.
