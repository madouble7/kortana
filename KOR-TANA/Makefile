# ============================================
# Kor'tana - Makefile
# ============================================
# Common Docker commands and workflows

.PHONY: help build up down restart logs clean test deploy-dev deploy-prod

# Default target
help:
	@echo "Kor'tana Docker Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make build         - Build all Docker images"
	@echo "  make up            - Start development environment"
	@echo "  make up-monitoring - Start with monitoring stack"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - Show logs from all services"
	@echo "  make logs-backend  - Show backend logs"
	@echo "  make logs-frontend - Show frontend logs"
	@echo "  make clean         - Remove containers, volumes, and images"
	@echo "  make test          - Run tests in containers"
	@echo "  make deploy-dev    - Deploy development environment"
	@echo "  make deploy-prod   - Deploy production environment"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-db      - Open PostgreSQL shell"
	@echo "  make backup-db     - Backup database"
	@echo "  make restore-db    - Restore database from backup"

# Build all images
build:
	@echo "Building Docker images..."
	@bash scripts/build-images.sh

# Start development environment
up:
	@echo "Starting development environment..."
	docker-compose up -d

# Start with monitoring
up-monitoring:
	@echo "Starting development with monitoring..."
	docker-compose --profile monitoring up -d

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose down

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f postgres

# Clean everything
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: clean
	@echo "Removing all Kortana images..."
	docker images | grep kortana | awk '{print $$3}' | xargs -r docker rmi -f

# Run tests
test:
	@echo "Running tests in Docker..."
	docker-compose exec backend pytest
	docker-compose exec frontend npm test

# Deploy commands
deploy-dev:
	@bash scripts/deploy.sh development

deploy-prod:
	@bash scripts/deploy.sh production

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-db:
	docker-compose exec postgres psql -U kortana -d kortana_db

# Database management
backup-db:
	@echo "Backing up database..."
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U kortana kortana_db > backups/kortana_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup complete!"

restore-db:
	@echo "Restoring database..."
	@read -p "Enter backup file path: " backup; \
	docker-compose exec -T postgres psql -U kortana kortana_db < $$backup
	@echo "Restore complete!"

# Check service health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/api/health || echo "Backend: DOWN"
	@curl -f http://localhost:3000/health || echo "Frontend: DOWN"
	@docker-compose exec redis redis-cli ping || echo "Redis: DOWN"
	@docker-compose exec postgres pg_isready -U kortana || echo "PostgreSQL: DOWN"

# Show service status
status:
	@echo "Service Status:"
	@docker-compose ps

# Install/Update dependencies
update-deps:
	@echo "Updating backend dependencies..."
	docker-compose exec backend pip install -r requirements.txt
	@echo "Updating frontend dependencies..."
	docker-compose exec frontend npm install

# View resource usage
stats:
	docker stats --no-stream

# Prune unused resources
prune:
	docker system prune -a --volumes
