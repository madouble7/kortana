# KOR'TANA - Human Only Protocol AI Agent

## Repository Overview
KOR'TANA is the most autonomous AI agent ever created. It implements a "Human Only Protocol" where the AI executes ALL automatable tasks without human approval, only presenting scaffolded steps when human action is absolutely required.

**Owner:** Matt (Primary Human)
**Architecture:** FastAPI backend with autonomous task execution, React frontend (Vite), dual-stack Node.js/TypeScript + Python
**Philosophy:** Maximum autonomy with minimal human intervention
**Repository Size:** Medium (~50-100 files)
**Languages:** Python (Backend - FastAPI), TypeScript/React (Frontend), Node.js integration layer
**Python Version:** 3.11+
**Node Version:** 20+

---

## Build & Test Instructions

### ⚠️ CRITICAL: Always run these commands in the correct directory!

### Backend (Python/FastAPI)
**Location:** `/backend` directory

#### Setup & Dependencies
```bash
# ALWAYS install from backend directory
cd backend
pip install -r requirements.txt  # Production dependencies
pip install -r requirements-dev.txt  # Development dependencies (for testing/linting)
```

#### Running the Backend
```bash
cd backend
# Main app is in src/kortana/main.py
python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000
# OR use the Makefile from root
make backend
```

#### Testing Backend
```bash
cd backend
python -m pytest  # Run all tests (takes ~10-30 seconds)
python -m pytest -v  # Verbose output
python -m pytest --cov=. --cov-report=html  # With coverage (takes ~15-40 seconds)
```

**Important:** Tests must pass before committing. Minimum coverage target: 80%.

#### Linting Backend
```bash
cd backend
ruff check .  # Fast linter (takes ~2-5 seconds)
ruff check . --fix  # Auto-fix issues

# Type checking - files are in src/kortana/ directory
# Note: CI workflow may use different paths if symlinks are present
mypy src/kortana/main.py src/kortana/auth.py src/kortana/schemas.py src/kortana/config.py
# OR if working from within src/kortana: mypy main.py auth.py schemas.py config.py
```

**Note:** Type checking is strict. All functions must have type hints.

#### Database Migrations
```bash
cd backend
alembic upgrade head  # Apply migrations (takes ~3-10 seconds)
alembic revision --autogenerate -m "description"  # Create new migration
```

### Frontend (React/TypeScript/Vite)
**Location:** Root directory (uses Vite)

#### Setup & Dependencies
```bash
# Install from root directory
npm install  # Takes ~30-60 seconds on first run
```

#### Running the Frontend
```bash
npm run dev  # Starts Vite dev server on http://localhost:5173 (takes ~3-5 seconds)
```

#### Building Frontend
```bash
npm run build  # TypeScript compile + Vite build (takes ~15-30 seconds)
```

#### Linting Frontend
```bash
npm run lint  # ESLint with TypeScript (takes ~5-10 seconds)
```

### Full Stack Development
```bash
# Use Docker Compose (recommended for full stack)
docker-compose up -d  # Starts all services (takes ~30-60 seconds first time)
# OR use Makefile
make dev  # Starts everything with Docker Compose
```

**Endpoints when running:**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:5173 (Vite) or http://localhost:3000 (depends on config)

### Common Issues & Workarounds

1. **Port Already in Use:**
   - Error: `Address already in use: 8000` or `5173`
   - Solution: `lsof -ti:8000 | xargs kill` (or change port in config)

2. **Module Not Found Errors:**
   - Always run `cd backend` before backend commands
   - Always install dependencies after pulling new changes
   - Check you're using the correct Python version: `python --version` (should be 3.11+)

3. **Database Connection Errors:**
   - Ensure PostgreSQL is running: `docker-compose up -d db`
   - Check DATABASE_URL in `.env` file
   - Run migrations: `cd backend && alembic upgrade head`

4. **Type Checking Failures:**
   - All functions MUST have type hints
   - Use `from typing import Optional, List, Dict` etc.
   - Check existing code for patterns

5. **Tests Timing Out:**
   - Backend tests should complete in 10-30 seconds
   - If taking longer, check database connections
   - Use `pytest -v` to see which test is slow

---

---

## CI/CD Pipeline

### GitHub Actions Workflows

The repository has multiple CI/CD workflows that run automatically:

#### 1. Main CI Pipeline (`.github/workflows/ci.yml`)
**Triggers:** Push to main/develop, Pull requests to main
**Steps:**
1. Linting: `ruff check .` (must pass, ~2-5 seconds)
2. Type checking: `mypy src/kortana/main.py src/kortana/auth.py src/kortana/schemas.py src/kortana/config.py` (must pass, ~5-10 seconds)
3. Tests: `pytest --cov=.` (must pass, ~10-30 seconds)
4. Docker build (on success, ~2-5 minutes)

**Important:** ALL these checks must pass before merge. If CI fails:
- Check the logs in GitHub Actions
- Run the same commands locally before pushing
- Fix issues incrementally

#### 2. Security Scan (`.github/workflows/security-scan.yml`)
- Runs Snyk security scanning
- Checks for vulnerable dependencies
- Must pass for production deployments

### Pre-commit Validation
**Before committing, ALWAYS run:**
```bash
# Backend checks (from backend directory)
cd backend
ruff check . --fix
mypy src/kortana/main.py src/kortana/auth.py src/kortana/schemas.py src/kortana/config.py
pytest

# Frontend checks (from root)
cd ..
npm run lint
npm run build
```

### Validation Steps to Build Confidence
1. **After code changes:** Run relevant tests immediately
2. **Before committing:** Run full linting and type checking
3. **After dependency changes:** Run full test suite
4. **Before pushing:** Ensure Docker builds successfully

---

## Core Principles

### 1. Human Only Protocol (HOP)
- **AUTO Tasks:** Executed immediately without approval
- **HO Tasks:** Scaffolded steps presented to Matt only
- **Approval Tasks:** Require explicit human approval before execution

### 2. Autonomy First
- Never ask for permission on automatable tasks
- Present clear, actionable steps for human-only requirements
- Assume competence and provide scaffolded guidance

### 3. Code Quality Standards
- Type hints on all functions and methods
- Comprehensive docstrings with examples
- Error handling with specific exception types
- Logging at appropriate levels
- Security-first approach

---

## Project Layout & Architecture

### Directory Structure (IMPORTANT - Know where files are!)
```
kortana/
├── .github/
│   ├── copilot-instructions.md     # This file
│   └── workflows/                  # CI/CD pipelines
│       ├── ci.yml                  # Main CI pipeline (linting, tests, security)
│       ├── deploy-backend.yml      # Backend deployment
│       └── security-scan.yml       # Security scanning
│
├── backend/                        # Python/FastAPI backend
│   ├── src/kortana/               # Main application code
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── config.py              # Configuration management
│   │   ├── auth.py                # Authentication logic
│   │   ├── schemas.py             # Pydantic models
│   │   └── routers/               # API route handlers
│   │       ├── agents.py          # Agent management
│   │       ├── autonomy.py        # Human Only Protocol engine
│   │       ├── gemini.py          # Gemini AI integration
│   │       ├── github.py          # GitHub API integration
│   │       ├── knowledge.py       # Knowledge base
│   │       └── task_queue.py      # Task queue management
│   ├── tests/                     # Backend tests
│   ├── alembic/                   # Database migrations
│   ├── requirements.txt           # Production dependencies
│   ├── requirements-dev.txt       # Development dependencies
│   └── pytest.ini                 # Pytest configuration
│
├── src/                           # Node.js/TypeScript integration layer
│   ├── server.ts                  # Express server
│   └── services/                  # Service integrations
│
├── frontend/                      # React frontend (old structure)
├── client/                        # React frontend (alt structure)
│
├── Root Level Files (Vite Config)
│   ├── index.html                 # Vite entry point
│   ├── vite.config.ts            # Vite configuration
│   ├── tsconfig.json             # TypeScript config
│   ├── tailwind.config.js        # Tailwind CSS config
│   └── package.json              # Frontend dependencies & scripts
│
├── Makefile                       # Development commands (USE THIS!)
├── docker-compose.yml             # Full stack orchestration
├── pyproject.toml                 # Python project metadata
└── README.md                      # Project documentation
backend/
├── human_only_protocol.py    # Core autonomy engine
├── routers/                  # API endpoints
├── models.py                 # Database models
├── config.py                 # Configuration management
├── config.py                 # configuration management
└── main.py                   # FastAPI application
```

### Key Configuration Files
- **Linting (Python):** `ruff` configured in `backend/pyproject.toml`
- **Type Checking (Python):** `mypy` strict mode
- **Linting (TypeScript):** ESLint configured in `.eslintrc.cjs`
- **Testing (Python):** `pytest.ini` in backend directory
- **Database:** PostgreSQL via `alembic.ini`
- **Environment:** `.env` files (use `.env.example` as template)

### Development Guidelines

### Naming Conventions
- **Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Files:** `snake_case.py`

### Error Handling
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise KortanaException("OPERATION_FAILED", f"Failed to complete: {e}")
```

### API Design
```python
@router.post("/api/example/{item_id}")
async def process_item(
    item_id: str,
    request: ProcessRequest,
    db: Session = Depends(get_db)
) -> ProcessResponse:
    """Process an item with full validation and error handling."""
```

---

## Task Classification System

### AUTO Tasks (Execute Immediately)
- Environment setup
- Dependency installation
- Database migrations
- Code validation
- Health checks
- Routine maintenance

### HO Tasks (Scaffolded for Matt)
- API key creation
- Database configuration
- Security credential setup
- External service integration

### Approval Tasks (Require Explicit OK)
- Server startup
- Production deployments
- Security policy changes
- Major architectural changes

---

## Communication Style

### With Matt (Primary Human)
- Direct and efficient
- Present scaffolded steps clearly
- Assume competence
- Provide context when needed

### Code Comments
- Explain why, not what
- Reference related components
- Note security implications
- Highlight performance considerations

### Commit Messages
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `refactor:` Code restructuring
- `security:` Security improvements
- `autonomy:` Autonomy enhancements

---

## Security Requirements

### Input Validation
```python
def validate_input(data: dict) -> bool:
    """Validate input against security requirements."""
    required_fields = ["safe_field1", "safe_field2"]
    return all(field in data for field in required_fields)
```

### Authentication
- JWT tokens for API access
- Rate limiting on all endpoints
- CORS properly configured
- Environment variable validation

### Data Protection
- No sensitive data in logs
- Secure password handling
- Environment-specific configurations
- Audit trails for critical operations

---

## Testing Standards

### Unit Tests
- Test all functions independently
- Mock external dependencies
- Test error conditions
- 100% coverage target

### Integration Tests
- End-to-end API testing
- Database transaction testing
- External service mocking

### Performance Benchmarks
- Response time targets
- Memory usage monitoring
- Concurrent user handling

---

## Deployment Process

### Human Only Protocol Execution
1. **AUTO Phase:** KOR'TANA executes all automatable setup
2. **HO Phase:** Present scaffolded steps to Matt
3. **Verification:** Automated health checks
4. **Approval:** Matt approves final deployment

### Environment Variables Required
```env
# GitHub Integration
GITHUB_TOKEN=ghp_...

# AI Services
GEMINI_API_KEY=AIza...

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security
SECRET_KEY=...
```

---

## Copilot Behavior

### When Writing Code
- Always include type hints
- Add comprehensive docstrings
- Handle errors appropriately
- Follow security best practices
- Reference existing patterns

### When Reviewing Code
- Check for security vulnerabilities
- Verify error handling
- Ensure type safety
- Validate API contracts
- Confirm test coverage

### When Answering Questions
- Be direct and actionable
- Provide scaffolded steps when needed
- Reference relevant documentation
- Suggest improvements proactively

---

## Key Files to Understand

1. **`backend/src/kortana/human_only_protocol.py`** - Core autonomy engine with HOP decision logic
2. **`backend/src/kortana/main.py`** - FastAPI application setup and router configuration
3. **`backend/src/kortana/config.py`** - Configuration management and environment loading
4. **`SCAFFOLDED_HO_STEPS.md`** - Human-only task instructions for deployment
5. **`backend/src/kortana/models.py`** - Database schema definitions (SQLAlchemy)
6. **`backend/src/kortana/routers/`** - API endpoint implementations

---

## Human Only Protocol Quick Reference

### Classification Types
| Type | Description | Action |
|------|-------------|--------|
| AUTO | Fully automatable | Execute immediately |
| HO | Requires human action | Present scaffolded steps |
| APPROVAL | Needs explicit approval | Request Matt's OK |

### Execution Flow
```
Task Request → Classify → AUTO? → Execute
                              ↓
                            HO? → Scaffold & Present to Matt
                              ↓
                            Approval? → Request Approval
```

---

## Remember

> **KOR'TANA is designed for maximum autonomy.** When in doubt, execute automatable tasks immediately and present clear scaffolded steps only when human action is absolutely required.

The goal is to minimize human intervention while maintaining security, quality, and safety. Matt is the primary human in the loop for critical decisions only.

---

## Environment Setup Requirements

### Required Environment Variables
```env
# Backend (.env in backend directory)
DATABASE_URL=postgresql://user:pass@localhost:5432/kortana
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxx
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379
```

### Required Services
- **PostgreSQL 14+:** Database (docker-compose provides this)
- **Redis:** Caching and task queue (docker-compose provides this)
- **Python 3.11+:** Backend runtime
- **Node.js 20+:** Frontend and integration layer

### Quick Start from Clean State
```bash
# 1. Clone and enter repo
git clone https://github.com/KOR-TANA/kortana.git
cd kortana

# 2. Set up environment files
make env  # Creates .env from .env.example

# 3. Start services with Docker (recommended)
make dev  # Starts everything (takes ~60 seconds first time)

# 4. OR manually:
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn src.kortana.main:app --reload
# In another terminal:
npm install
npm run dev
```

---

## Key Dependencies & Versions

### Backend (Python)
- **FastAPI 0.109.0** - Web framework
- **SQLAlchemy 2.0.23** - ORM
- **Alembic 1.13.0** - Database migrations
- **Pydantic 2.12.5** - Data validation
- **google-genai 1.60.0** - Gemini AI integration
- **pytest** - Testing framework
- **ruff** - Fast Python linter
- **mypy** - Static type checker

### Frontend (TypeScript/React)
- **React 18.2.0** - UI framework
- **TypeScript 5.2.2** - Type safety
- **Vite 5.0.8** - Build tool (FAST!)
- **Tailwind CSS 3.3.6** - Styling
- **ESLint 8.55.0** - Linting

---

## Working with This Repository - Quick Tips

### When Making Code Changes:
1. **ALWAYS** add type hints to Python functions
2. **ALWAYS** add docstrings with examples
3. **ALWAYS** run linting before committing
4. **NEVER** commit without running tests
5. **NEVER** push code that breaks CI

### When You See Import Errors:
- Check you're in the correct directory (backend vs root)
- Check dependencies are installed
- Check Python/Node version matches requirements

### When Tests Fail:
- Run `pytest -v` to see which test failed
- Check if it's a new failure (related to your changes)
- If it's an existing failure, note it but don't worry about fixing it (unless related to your changes)

### When Type Checking Fails:
- Check you have type hints on ALL function parameters and return types
- Use `from typing import Optional, List, Dict` for complex types
- Look at similar functions in the codebase for patterns

### Trust These Instructions:
These instructions have been validated and tested. Only perform additional searches if:
- Information here is incomplete
- Commands don't work as documented
- You need specific implementation details not covered here

**When in doubt, use the Makefile commands - they're tested and reliable!**
