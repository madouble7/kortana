# Kor'tana Development Guide

**A comprehensive guide to developing on the Kor'tana multimodal AI system**

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Project Structure](#project-structure)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- VS Code (recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/kor-tana.git
cd kor-tana

# Run setup script
python scripts/setup/setup-environment.py

# Or use Make
make install-dev
make env

# Start development environment
make dev
```

### Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Frontend
cd frontend
npm install

# Install pre-commit hooks
pre-commit install
```

---

## Project Structure

```
kortana/
├── backend/                    # FastAPI Python backend
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── routers/               # API route handlers
│   │   ├── agents.py          # Agent management
│   │   ├── autonomy.py        # Autonomous operations
│   │   ├── gemini.py          # Google Gemini integration
│   │   ├── github.py          # GitHub integration
│   │   ├── knowledge.py       # Knowledge base
│   │   ├── memory.py          # Memory/storage
│   │   └── task_queue.py      # Task management
│   ├── tests/                 # Unit tests
│   ├── requirements.txt        # Production dependencies
│   ├── requirements-dev.txt    # Development dependencies
│   └── README.md              # Backend documentation
│
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx            # Root component
│   │   ├── components/        # UI components
│   │   └── services/          # API services
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md              # Frontend documentation
│
├── vscode-extension/          # VS Code extension
│   ├── src/
│   └── package.json
│
├── scripts/                   # Utility scripts
│   ├── setup/                # Setup scripts
│   ├── deployment/           # Deployment scripts
│   └── testing/              # Test scripts
│
├── docs/                      # Documentation
│   ├── governance/           # System governance
│   ├── workflows/            # Development workflows
│   └── architecture/         # Architecture docs
│
├── Dockerfile                # Production Docker image
├── docker-compose.yml        # Local development
├── Makefile                  # Common commands
├── pyproject.toml            # Python configuration
└── .pre-commit-config.yaml   # Git hooks

```

---

## Backend Development

### Running the Backend

```bash
# Development with auto-reload
cd backend
uvicorn main:app --reload

# Or use Make
make backend

# Or use Docker Compose
docker-compose up backend
```

Backend runs on `http://localhost:8000`

### API Documentation

Interactive API docs: `http://localhost:8000/docs` (Swagger UI)
Alternative docs: `http://localhost:8000/redoc` (ReDoc)

### Adding New Endpoints

1. Create a new router file in `routers/`
2. Define your endpoint functions
3. Include router in `main.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Item(BaseModel):
    name: str
    description: Optional[str] = None

@router.post("/items")
async def create_item(item: Item):
    return {"item": item, "created": True}

# In main.py:
from routers import your_router
app.include_router(your_router.router, prefix="/api/your", tags=["your"])
```

### Database

```bash
# Create migrations
cd backend
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Environment Variables

Copy `.env.example` to `.env` and update:

```bash
cp backend/.env.example backend/.env
# Edit .env with your API keys
```

---

## Frontend Development

### Running the Frontend

```bash
# Development with hot reload
cd frontend
npm start

# Or use Make
make frontend

# Or use Docker Compose
docker-compose up frontend
```

Frontend runs on `http://localhost:3000`

### Project Structure

```
frontend/src/
├── App.tsx                 # Root component
├── components/
│   ├── GitHubDashboard.tsx # GitHub monitoring
│   ├── MemoryBrowser.tsx   # Knowledge base
│   ├── PrayerAgentStatus.tsx
│   └── SystemStatus.tsx
├── services/
│   └── apiService.ts       # Backend API calls
├── types/                  # TypeScript types
└── styles/                 # CSS/styling
```

### TypeScript Strict Mode

The project uses strict TypeScript. Run type checking:

```bash
cd frontend
npx tsc --noEmit
```

### Component Development

```typescript
import React from 'react';

interface Props {
  title: string;
  count?: number;
}

export const MyComponent: React.FC<Props> = ({ title, count = 0 }) => {
  return <div>{title}: {count}</div>;
};
```

---

## Testing

### Running Tests

```bash
# All tests
make test

# Backend tests
make test-backend

# Frontend tests
make test-frontend

# With coverage
make coverage
```

### Writing Tests

**Backend (pytest):**

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
```

**Frontend (Jest/Vitest):**

```typescript
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

test('renders title', () => {
  render(<MyComponent title="Test" />);
  expect(screen.getByText('Test')).toBeInTheDocument();
});
```

### Test Coverage

Target: 80%+ coverage

```bash
# Generate coverage report
make coverage

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Code Quality

### Formatting

```bash
# Format code with Black
make format

# Format specific file
black backend/main.py --line-length 100
```

### Linting

```bash
# Run Ruff linter
make lint

# Auto-fix issues
ruff check backend --fix
```

### Type Checking

```bash
# Run MyPy
make type-check

# Strict mode
mypy backend --strict
```

### Pre-commit Hooks

Automatically runs formatting, linting, and type checking:

```bash
# Setup (one-time)
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Deployment

### Local Docker Build

```bash
# Build image
docker build -t kor-tana:latest .

# Run image
docker run -p 8000:8000 kor-tana:latest

# With environment
docker run -p 8000:8000 --env-file .env kor-tana:latest
```

### Cloud Deployment (Google Cloud Run)

```bash
# Build and deploy
gcloud run deploy kortana-backend \
  --source . \
  --platform managed \
  --region us-west1 \
  --allow-unauthenticated

# View logs
gcloud run logs read kortana-backend --limit 100
```

### GitHub Actions

Automatic deployment on push to main:

- Runs tests
- Builds Docker image
- Pushes to Google Cloud Registry
- Deploys to Cloud Run
- Health checks

---

## Troubleshooting

### Backend Issues

**Import errors:**

```bash
# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall dependencies
pip install -r requirements-dev.txt
```

**Database connection issues:**

```bash
# Check database is running
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres
```

**Port already in use:**

```bash
# Find process on port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Frontend Issues

**Dependencies not installing:**

```bash
# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

**Port conflicts:**

```bash
# Run on different port
PORT=3001 npm start
```

### Docker Issues

**Rebuild image:**

```bash
docker-compose build --no-cache

docker-compose up --force-recreate
```

**View logs:**

```bash
docker-compose logs -f <service>
docker-compose logs -f backend
```

---

## Common Commands

```bash
# Development
make dev                 # Start all services
make backend            # Backend only
make frontend           # Frontend only

# Testing
make test              # Run all tests
make coverage          # Coverage report

# Code Quality
make lint              # Linting
make format            # Code formatting
make type-check        # Type checking

# Database
make migrate           # Apply migrations
make migrate-create    # Create migration

# Cleanup
make clean             # Remove cache files
make clean-docker      # Remove Docker resources
```

## Reference

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [API Documentation](http://localhost:8000/docs)
- [Optimization Roadmap](OPTIMIZATION_ROADMAP.md)
- [Production Readiness](PRODUCTION_READINESS.md)

---

**Last Updated:** January 14, 2026
