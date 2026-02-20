# Print Advisor - Makefile
.PHONY: help build up down logs smoke migrate collectstatic clean test lint nginx-setup nginx-up nginx-down nginx-logs nginx-test deploy-all ingest-setup ingest-install ingest-run ingest-status

# Default target
help:
	@echo "Print Advisor - Available commands:"
	@echo "  build        - Build Docker images"
	@echo "  up           - Start all services"
	@echo "  up-build     - Start all services with build"
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
	@echo "  deploy-all   - Deploy everything (Nginx + App) with migrations"
	@echo "  ingest-setup - Create transit ingest directories"
	@echo "  ingest-install - Install ingest systemd timer"
	@echo "  ingest-run   - Run ingest mover once"
	@echo "  ingest-status - Show ingest timer and logs"
	@echo ""
	@echo "Nginx Reverse Proxy commands:"
	@echo "  nginx-setup  - Create reverse-proxy-network (one-time setup)"
	@echo "  nginx-up     - Start Nginx reverse proxy"
	@echo "  nginx-down   - Stop Nginx reverse proxy"
	@echo "  nginx-logs   - Show Nginx logs"
	@echo "  nginx-test   - Test Nginx configuration"

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

# Nginx Reverse Proxy commands
nginx-setup:
	@echo "Creating reverse-proxy-network..."
	@docker network create reverse-proxy-network 2>/dev/null || echo "Network already exists"

nginx-up: nginx-setup
	@echo "Starting Nginx reverse proxy..."
	@docker compose -f docker-compose.proxy.yml up -d
	@echo "Nginx started. Access application at http://localhost/"

nginx-down:
	@echo "Stopping Nginx reverse proxy..."
	@docker compose -f docker-compose.proxy.yml down

nginx-logs:
	@docker compose -f docker-compose.proxy.yml logs -f nginx

nginx-test:
	@echo "Testing Nginx configuration..."
	@docker compose -f docker-compose.proxy.yml exec nginx nginx -t || echo "Nginx container not running. Start it with 'make nginx-up'"

# Deploy everything: Nginx + App + Migrations
deploy-all: nginx-setup nginx-up build up
	@echo "Waiting for services to start..."
	@sleep 30
	@echo "Running migrations..."
	@docker compose exec web python manage.py migrate --noinput
	@echo ""
	@echo "✅ Deployment complete!"
	@echo "Access application at: http://localhost/"
	@echo "Create superuser: make shell (then: python manage.py createsuperuser)"

# Ingest transit pipeline commands
ingest-setup:
	@sudo ./scripts/setup_transit_ingest.sh /srv/advisor

ingest-install:
	@sudo cp infrastructure/systemd/advisor-ingest.env.example /etc/default/advisor-ingest
	@sudo cp infrastructure/systemd/advisor-ingest-mover.service /etc/systemd/system/
	@sudo cp infrastructure/systemd/advisor-ingest-mover.timer /etc/systemd/system/
	@sudo systemctl daemon-reload
	@sudo systemctl enable --now advisor-ingest-mover.timer

ingest-run:
	@sudo /opt/advisor-dj/scripts/ingest_mover.sh

ingest-status:
	@systemctl status advisor-ingest-mover.timer --no-pager
	@journalctl -u advisor-ingest-mover.service -n 30 --no-pager
