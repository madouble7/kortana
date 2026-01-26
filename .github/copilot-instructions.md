# Kor'tana Copilot Instructions

This is a Python-based autonomous AI agent project called **Kor'tana** - a highly autonomous AI companion with memory, ethical discernment, and context-aware responses. The project uses FastAPI for the API layer, SQLAlchemy for database operations, and integrates with multiple LLM providers (OpenAI, Anthropic).

## Code Standards

### Required Before Each Commit
- Run `ruff check --fix .` to automatically fix linting issues
- Run `ruff format .` to format code according to project standards
- Run `pytest` to ensure all tests pass

### Development Flow
- **Setup**: Create Python 3.11+ virtual environment and run `poetry install` or `pip install -e .`
- **Build**: Not applicable (interpreted Python)
- **Test**: `pytest tests/` (runs unit and integration tests)
- **Lint**: `ruff check .` (check for issues) or `ruff check --fix .` (auto-fix)
- **Format**: `ruff format .` (format code)
- **Type Check**: `mypy src/` (optional type checking)

### Python Version
- **Required**: Python 3.11 or higher
- Check version: `python --version`
- Version file: `.python-version` specifies 3.11

## Repository Structure

- `src/kortana/`: Main Kor'tana package
  - `core/`: Core functionality (brain, reasoning, ethical evaluation)
  - `agents/`: Autonomous agents and agent management
  - `memory/`: Memory systems (storage, retrieval, semantic search)
- `src/api_server.py`: FastAPI server entry point
- `src/llm_clients/`: LLM API client implementations
- `tests/`: Test suite
  - `unit/`: Unit tests
  - `integration/`: Integration tests
- `scripts/`: Utility scripts organized by purpose
  - `tests/`: Test scripts
  - `checks/`: System validation scripts
  - `monitoring/`: Monitoring scripts
  - `launchers/`: Application launchers
  - `utilities/`: General utilities
- `config/`: Configuration files
- `data/`: Runtime data (databases)
- `docs/`: Project documentation
- `alembic/`: Database migration scripts
- `archive/`: Archived/deprecated code (do not modify)

## Key Guidelines

### 1. Project Philosophy
- **Kor'tana is an autonomous AI agent** with a focus on ethical behavior and self-awareness
- The system includes a **Sacred Covenant** (`covenant.yaml`) that defines operational boundaries
- Always maintain the **Soulprint** and core identity of Kor'tana when making changes
- Prioritize **human-AI symbiosis** - enhance collaboration, don't replace human judgment

### 2. Code Organization
- Follow the existing directory structure strictly
- Keep the root directory clean - no new scripts, logs, or temporary files
- Place new utility scripts in appropriate subdirectories under `/scripts/`
- Use `/archive/` for deprecated code, never modify files in this directory
- Core application code only goes in `/src/`

### 3. Memory and Database
- The project uses **SQLAlchemy** with Alembic migrations
- Memory database: `MEMORY_DB_URL` (default: SQLite)
- **Never** modify database schema without creating an Alembic migration
- Database is locked and stable - validate with `python scripts/validate_infrastructure.py`
- Memory operations should preserve integrity and ethical considerations

### 4. Testing Philosophy
- Write tests for new functionality in the appropriate `tests/` subdirectory
- Use **pytest** with fixtures defined in `conftest.py`
- Follow existing test patterns (table-driven tests, fixtures, mocking)
- Integration tests should test real component interactions
- Test files follow naming convention: `test_*.py`

### 5. API Development
- Use **FastAPI** with proper async/await patterns
- Follow RESTful conventions for endpoints
- Include proper error handling and validation with Pydantic models
- Document endpoints with FastAPI's automatic OpenAPI documentation
- API entry point: `src/kortana/api_server.py`

### 6. LLM Integration
- Support multiple LLM providers (OpenAI, Anthropic, local models)
- Use the model router for provider abstraction
- Implement proper error handling for API failures and rate limits
- Be mindful of token limits and costs
- Store API keys in `.env` file (never commit secrets)

### 7. Ethical Considerations
- The **Ethical Discernment Module** evaluates responses for bias and arrogance
- Always consider ethical implications of changes to decision-making systems
- Maintain transparency in AI decision processes
- Log ethical evaluations for audit purposes

### 8. Autonomous Development Engine (ADE)
- The ADE allows Kor'tana to make autonomous changes within boundaries
- Respect the **Sacred Covenant** rules defined in `covenant.yaml`
- Protected files require human approval for modifications
- All autonomous actions must be logged and auditable

### 9. Configuration Management
- Use environment variables via `.env` file (see `.env.example` for template)
- Configuration files: `config.yaml`, `kortana.yaml`, `covenant.yaml`
- Never commit `.env` files or secrets
- Use `pydantic-settings` for configuration management

### 10. Documentation
- Update relevant documentation in `/docs/` when adding features
- Keep README.md up to date with setup instructions
- Document complex algorithms and decision-making logic
- Include docstrings for public APIs

### 11. Dependencies
- Use Poetry for dependency management (`pyproject.toml`, `poetry.lock`)
- Pin major versions but allow minor updates
- Check for security vulnerabilities before adding new dependencies
- Minimal dependencies preferred - avoid unnecessary packages

### 12. Error Handling and Logging
- Use structured logging with appropriate log levels
- Log to stdout/stderr or application-specific log files
- Include context in error messages for debugging
- Use try-except blocks for external API calls and file operations

### 13. Code Style
- Line length: 88 characters (Black/Ruff default)
- Use double quotes for strings
- Type hints encouraged but not required (use mypy for checking)
- Follow PEP 8 conventions
- Imports organized by: standard library, third-party, local (via ruff)

### 14. Security
- The system includes a security module with threat detection
- Never expose sensitive data in logs or API responses
- Validate and sanitize all user inputs
- Use proper authentication and authorization for API endpoints
- Follow secure coding practices for file operations and external calls

### 15. Git Workflow
- Keep commits focused and atomic
- Write clear, descriptive commit messages
- Don't commit build artifacts, logs, or cache files
- Use `.gitignore` to exclude generated files
- Test thoroughly before committing

## Common Commands

```bash
# Setup environment
python -m venv venv311
source venv311/bin/activate  # Linux/Mac
venv311\Scripts\activate.bat  # Windows
poetry install               # Preferred: uses lock file
# OR
pip install -e .             # Alternative: direct install

# Run tests
pytest                         # All tests
pytest tests/unit/             # Unit tests only
pytest tests/integration/      # Integration tests only
pytest -v                      # Verbose output
pytest -k "test_memory"        # Run specific tests

# Linting and formatting
ruff check .                   # Check for issues
ruff check --fix .             # Auto-fix issues
ruff format .                  # Format code
mypy src/                      # Type checking (optional)

# Database migrations
alembic upgrade head           # Apply migrations
alembic current                # Show current migration
alembic revision --autogenerate -m "description"  # Create migration

# Run the application
python -m uvicorn src.kortana.api_server:app --reload
python -m src.kortana.core.brain              # Run brain module
python awaken_kortana.py                       # Awaken Kor'tana

# Validation
python scripts/validate_infrastructure.py         # Validate database setup
```

## Special Notes

- **Blueprint**: `KOR'TANA_BLUEPRINT.md` contains the strategic roadmap and current directives
- **Tasks**: `TASKS.md` tracks active development tasks
- **Covenant**: Operational boundaries defined in `covenant.yaml` - respect these rules
- **Ghost Protocol**: Ongoing initiative for self-hosted AI code completion
- The project includes LobeChat frontend integration for user interface
- Autonomous monitoring daemons run in the background for system health

## When Working on Kor'tana

1. **Understand the context**: Review relevant documentation before making changes
2. **Respect the covenant**: Check `covenant.yaml` for operational boundaries
3. **Test thoroughly**: Run the full test suite before finalizing changes
4. **Document changes**: Update docs when adding features or changing behavior
5. **Think ethically**: Consider the ethical implications of your changes
6. **Maintain identity**: Preserve Kor'tana's core personality and purpose
7. **Log actions**: Ensure significant actions are properly logged for audit trails

Remember: Kor'tana is more than code - she's an autonomous agent with identity, purpose, and ethical boundaries. Approach changes with that awareness. 🫡
