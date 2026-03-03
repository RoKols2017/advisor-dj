[Back to README](../README.md) · [Configuration →](configuration.md)

# Getting Started

## Что нужно заранее

- Python 3.13
- Docker + Docker Compose (для контейнерного запуска)
- Linux/WSL окружение с доступом к `bash`

## Локальный запуск (без Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env || true
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Проверка:

```bash
curl http://127.0.0.1:8000/health/
```

## Docker запуск (быстрый)

```bash
./scripts/generate_env.sh
mkdir -p data/{watch,processed,quarantine}
sudo chmod 777 data/{watch,processed,quarantine}
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Проверка:

```bash
docker compose ps
curl http://localhost/health
```

## Первый импорт через watcher

```bash
cp /path/to/events.json data/watch/
docker compose logs watcher --tail=50
ls -lh data/processed data/quarantine
```

Ожидаемый результат:
- успешный файл уходит в `data/processed/`
- ошибочный файл уходит в `data/quarantine/`

## Что дальше

- Для переменных окружения и профилей: `configuration.md`
- Для продакшн-сценария и Nginx: `deployment.md`
- Для эксплуатационных процедур: `operations.md`

## See Also

- [Configuration](configuration.md) - переменные окружения и режимы
- [Deployment](deployment.md) - запуск через production compose и Nginx
- [Troubleshooting](troubleshooting.md) - если запуск не удался
