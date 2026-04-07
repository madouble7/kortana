#!/bin/bash

# ============================================================================
# Kor'tana Docker Development Quick Reference
# ============================================================================

# SETUP (one-time)
# ============================================================================

# 1. Create .env from template
cp .env.example .env

# 2. Build all images
docker compose build

# 3. Start the full stack
docker compose up -d

# 4. Verify services are healthy
docker compose ps
docker compose logs -f


# DEVELOPMENT COMMANDS
# ============================================================================

# Start all services in foreground (see logs in real-time)
docker compose up

# Start services in background
docker compose up -d

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
docker compose logs -f redis

# Rebuild services after dependency changes
docker compose build

# Rebuild without cache
docker compose build --no-cache

# Run a one-off command (e.g., database migrations)
docker compose exec backend alembic upgrade head

# Access a service's shell
docker compose exec backend sh
docker compose exec frontend sh
docker compose exec postgres psql -U kortana -d kortana_db

# Check service status and resource usage
docker compose ps
docker stats


# DATABASE COMMANDS
# ============================================================================

# Connect to PostgreSQL
docker compose exec postgres psql -U kortana -d kortana_db

# Backup database
docker compose exec postgres pg_dump -U kortana kortana_db > backup.sql

# Restore database
docker compose exec -T postgres psql -U kortana kortana_db < backup.sql

# Reset database (delete all data)
docker compose down -v postgres
docker compose up -d postgres


# REDIS COMMANDS
# ============================================================================

# Connect to Redis CLI
docker compose exec redis redis-cli

# Clear all data
docker compose exec redis redis-cli FLUSHALL


# PRODUCTION DEPLOYMENT
# ============================================================================

# Copy production environment template
cp .env.prod.example .env.prod

# Edit .env.prod with real credentials
# nano .env.prod

# Build production image
docker build -t kortana-backend:latest -f Dockerfile.prod .

# Start production stack
docker compose -f docker-compose.prod.yml up -d

# Monitor production services
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f

# Stop production stack
docker compose -f docker-compose.prod.yml down


# TROUBLESHOOTING
# ============================================================================

# Check if Docker daemon is running
docker info

# View all containers (running and stopped)
docker ps -a

# View container logs
docker logs <container_id>

# Inspect a container
docker inspect <container_id>

# Check network connectivity
docker network ls
docker network inspect kortana-network

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Free up Docker disk space
docker system prune -a

# Check image size and layers
docker image history kortana-dev:test


# PERFORMANCE & OPTIMIZATION
# ============================================================================

# Monitor resource usage in real-time
docker stats

# Build with BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t kortana-backend:latest -f Dockerfile.prod .

# Push to Docker registry
docker tag kortana-backend:latest <registry>/kortana-backend:latest
docker push <registry>/kortana-backend:latest


# USEFUL VARIABLES
# ============================================================================

# Available in .env:
# DB_USER=kortana
# DB_PASSWORD=kortana_dev
# DB_NAME=kortana_db
# REDIS_PORT=6379
# API_PORT=8000
# FRONTEND_PORT=3000
# ENVIRONMENT=development (or production)
