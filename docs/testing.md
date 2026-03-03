[← Operations](operations.md) · [Back to README](../README.md) · [Security →](security.md)

# Testing

## Локальные тесты

```bash
pytest -q
pytest --cov=. --cov-report=term-missing --cov-fail-under=70
pytest tests/unit/ -q
pytest tests/integration/ -q
pytest -m "not slow" -q
```

## Проверки качества

```bash
ruff check .
black --check .
mypy .
```

## Smoke проверки в Docker

```bash
./scripts/smoke.sh
SMOKE_COMPOSE_FILE=docker-compose.prod.yml SMOKE_ENV_FILE=.env.prod ./scripts/smoke.sh
```

## Минимальный pre-release набор

- `pytest -q` проходит
- покрытие не ниже порога в `pytest.ini`
- health endpoint отвечает `200`
- watcher обрабатывает тестовый файл без ошибок

## Где смотреть результаты

- Отчет по проверкам: `TESTING_REPORT.md`
- CI pipeline: `.github/workflows/`

## See Also

- [Operations](operations.md) - smoke и post-deploy проверки
- [Troubleshooting](troubleshooting.md) - если тесты падают из-за окружения
- [Deployment](deployment.md) - проверки после запуска production-стека
