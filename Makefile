# Print Advisor - Makefile
.PHONY: help build up down logs smoke migrate collectstatic clean test lint

# Default target
help:
	@echo "Print Advisor - Available commands:"
	@echo "  build        - Build Docker images"
	@echo "  up           - Start all services"
	@echo "  down         - Stop all services"
	@echo "  logs         - Show logs from all services"
	@echo "  logs-web     - Show logs from web service"
	@echo "  logs-watcher - Show logs from watcher service"
	@echo "  logs-db      - Show logs from database service"
	@echo "  smoke        - Run smoke tests"
	@echo "  migrate      - Run database migrations"
	@echo "  collectstatic - Collect static files"
	@echo "  shell        - Open Django shell in web container"
	@echo "  test         - Run tests in web container"
	@echo "  lint         - Run linting and formatting"
	@echo "  clean        - Clean up containers and volumes"
	@echo "  restart      - Restart all services"

# Build Docker images
build:
	docker compose build

# Start all services
up:
	docker compose up -d

# Start with build
up-build:
	docker compose up --build -d

# Stop all services
down:
	docker compose down

# Show logs
logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

logs-watcher:
	docker compose logs -f watcher

logs-db:
	docker compose logs -f db

# Run smoke tests
smoke:
	@echo "Running smoke tests..."
	@./scripts/smoke.sh

# Database operations
migrate:
	docker compose exec web python manage.py migrate

collectstatic:
	docker compose exec web python manage.py collectstatic --noinput

# Django shell
shell:
	docker compose exec web python manage.py shell

# Run tests
test:
	docker compose exec web python -m pytest

# Linting and formatting
lint:
	docker compose exec web ruff check .
	docker compose exec web black --check .
	docker compose exec web mypy .

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Restart services
restart:
	docker compose restart

# Check service status
status:
	docker compose ps

# Show service health
health:
	@echo "Checking service health..."
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

