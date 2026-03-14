# Makefile for Kortana Development
.PHONY: help install dev test lint format clean docker-up docker-down migrate docs

help:
	@echo "Kor'tana Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install all dependencies"
	@echo "  make install-dev      - Install dev dependencies"
	@echo "  make env              - Create .env files from examples"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Run development servers (docker-compose)"
	@echo "  make docker-up        - Start Docker services"
	@echo "  make docker-down      - Stop Docker services"
	@echo "  make backend          - Run backend only"
	@echo "  make frontend         - Run frontend only"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          - Run database migrations"
	@echo "  make migrate-create   - Create new migration"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-frontend    - Run frontend tests"
	@echo "  make coverage         - Generate coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run linting checks"
	@echo "  make format           - Format code with Black"
	@echo "  make type-check       - Run MyPy type checking"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Remove cache and build files"
	@echo "  make clean-docker     - Remove Docker images and volumes"

# Setup
install:
	@echo "Installing production dependencies..."
	pip install -r backend/requirements.txt
	cd frontend && npm install

install-dev: install
	@echo "Installing development dependencies..."
	pip install -r backend/requirements-dev.txt

env:
	@echo "Creating .env files..."
	cp backend/.env.example backend/.env || true
	@echo "✅ Environment files configured (update with your values)"

# Development
dev: docker-up
	@echo "🚀 Kor'tana development environment started"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

backend:
	cd backend && uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm start

# Database
migrate:
	cd backend && alembic upgrade head

migrate-create:
	cd backend && alembic revision --autogenerate -m "$(message)"

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && pytest -v --cov=routers --cov-report=html

test-frontend:
	cd frontend && npm test -- --coverage

coverage:
	@echo "Backend coverage:"
	cd backend && pytest --cov=routers --cov-report=term-missing
	@echo "Frontend coverage:"
	cd frontend && npm test -- --coverage --watchAll=false

# Code Quality
lint:
	@echo "Running Ruff linter..."
	ruff check backend --fix
	@echo "Running MyPy type checker..."
	mypy backend --strict

format:
	@echo "Formatting code with Black..."
	black backend --line-length 100

type-check:
	@echo "Running type checking..."
	mypy backend --strict

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf backend/dist backend/build backend/*.egg-info
	cd frontend && rm -rf build dist
	@echo "✅ Cleanup complete"

clean-docker:
	@echo "Removing Docker resources..."
	docker-compose down -v
	@echo "✅ Docker cleanup complete"

.DEFAULT_GOAL := help
