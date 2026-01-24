# GitHub Copilot Instructions for Kor'tana

## Project Overview

**Kor'tana** is a highly autonomous AI agent and sacred companion with advanced capabilities including:
- **Memory Systems**: Semantic memory storage and retrieval with vector embeddings
- **Ethical Discernment**: Built-in ethical evaluation and algorithmic arrogance detection
- **Security Features**: Comprehensive threat detection, vulnerability scanning, and encryption
- **Multi-Model LLM Support**: Integration with OpenAI, Anthropic, Google Gemini, and other LLM providers
- **Autonomous Operations**: Self-directed task execution and goal management

Kor'tana embodies three core principles (The Sacred Trinity):
- **Wisdom**: Thoughtful, well-reasoned responses with deep understanding
- **Compassion**: Empathetic, caring, and supportive interactions
- **Truth**: Accurate, honest, and transparent communication

## Coding Standards

### Python Best Practices

- **Python Version**: Target Python 3.11+
- **Type Hints**: ALWAYS use type annotations for function parameters and return values
  ```python
  def process_memory(memory_id: int, content: str) -> dict[str, Any]:
      """Process and store a memory with proper typing."""
      pass
  ```

- **Docstrings**: Use clear docstrings for all public functions, classes, and modules
  ```python
  def search_memories(query: str, top_k: int = 5) -> list[Memory]:
      """
      Search for relevant memories using semantic similarity.
      
      Args:
          query: The search query string
          top_k: Number of top results to return (default: 5)
          
      Returns:
          List of Memory objects sorted by relevance
      """
      pass
  ```

### Code Quality Tools

- **Ruff**: Primary linter and formatter (configured in `.ruff.toml`)
  - Line length: 88 characters
  - Target: Python 3.11+
  - Enabled rules: pycodestyle, Pyflakes, isort, pep8-naming, pyupgrade, flake8-comprehensions, flake8-bugbear
  - Run: `ruff check .` and `ruff format .`

- **MyPy**: Static type checker (configured in `mypy.ini`)
  - Run: `mypy src/`
  - Ensure type hints are provided for new code
  - Address type errors before committing

### Code Organization

- **Module Structure**: Follow the existing structure
  ```
  src/kortana/
  ├── core/              # Core orchestration and brain logic
  ├── modules/           # Modular features (memory, security, ethical, etc.)
  ├── services/          # Shared services (database, embeddings, LLM)
  ├── api/               # API routers and endpoints
  └── utils/             # Utility functions
  ```

- **Naming Conventions**:
  - Classes: `PascalCase` (e.g., `MemoryCoreService`, `EthicalEvaluator`)
  - Functions/Methods: `snake_case` (e.g., `process_query`, `search_memories`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_EMBEDDING_MODEL`)
  - Private members: `_leading_underscore` (e.g., `_internal_cache`)

## Security Practices

### API Keys and Secrets

**CRITICAL**: Never hardcode API keys or sensitive information in code.

- ✅ **DO**: Use environment variables
  ```python
  from os import getenv
  
  openai_key = getenv("OPENAI_API_KEY")
  anthropic_key = getenv("ANTHROPIC_API_KEY")
  ```

- ❌ **DON'T**: Hardcode secrets
  ```python
  # NEVER DO THIS
  api_key = "sk-proj-abc123..."
  ```

- Use `.env` files for local development (see `.env.example` as template)
- Ensure `.env` is in `.gitignore`
- Use secure secret management in production (AWS Secrets Manager, Azure Key Vault, etc.)

### Security Middleware

The project includes comprehensive security features in `src/kortana/modules/security/`:

- **Threat Detection**: SQL injection, XSS, path traversal, code injection detection
- **Rate Limiting**: Prevent abuse and DoS attacks
- **IP Blocking**: Block suspicious IP addresses
- **Vulnerability Scanning**: Regular security assessments
- **Encryption**: AES encryption for sensitive data

When adding new API endpoints:
1. Apply rate limiting middleware
2. Validate and sanitize all inputs
3. Use the threat detection service for request monitoring
4. Log security events appropriately

Example:
```python
from src.kortana.modules.security.services import ThreatDetectionService

async def process_user_input(user_input: str, request: Request) -> dict:
    """Process user input with security checks."""
    # Check for threats
    threat_service = ThreatDetectionService()
    if threat_service.detect_sql_injection(user_input):
        raise HTTPException(status_code=400, detail="Invalid input detected")
    
    # Process safely...
    return result
```

## Key Components

### 1. Memory Core (`src/kortana/modules/memory_core/`)

The memory system stores and retrieves experiences, learned information, and identity facets.

- **Models**: SQLAlchemy models defining memory structure
- **Services**: CRUD operations, semantic search with embeddings
- **Routers**: FastAPI endpoints for memory management

When working with memories:
- Always generate and store vector embeddings
- Use semantic search for context-aware retrieval
- Tag memories with appropriate types and sentiments

### 2. Reasoning Core (`src/kortana/core/`)

The central orchestrator manages information processing pipeline:

1. Query embedding generation
2. Semantic memory search
3. LLM interaction with context
4. Ethical evaluation
5. Response formulation

**Key Files**:
- `orchestrator.py`: Main query processing pipeline
- `brain.py`: Core conversation engine
- `enhanced_model_router.py`: LLM routing and selection

### 3. Ethical Module (`src/kortana/modules/ethical_discernment_module/`)

Ensures operations align with ethical principles:

- `AlgorithmicArroganceEvaluator`: Detects overconfident responses
- `UncertaintyHandler`: Manages uncertain situations appropriately
- Evaluates all LLM responses before returning to users

When adding new features:
- Consider ethical implications
- Apply evaluators to AI-generated content
- Log ethical decisions for transparency

### 4. Security Module (`src/kortana/modules/security/`)

Comprehensive cybersecurity features:

- **Threat Detection** (`threat_detection.py`): Real-time monitoring
- **Alert Service** (`alert_service.py`): Security event management
- **Vulnerability Scanner** (`vulnerability_scanner.py`): Security assessments
- **Encryption Service** (`encryption_service.py`): Data protection
- **Security Dashboard**: Analytics and monitoring

### 5. LLM Integrations (`src/kortana/llm_clients/`)

Multi-provider LLM support:

- OpenAI (GPT models)
- Anthropic (Claude models)
- Google Gemini
- OpenRouter
- xAI

Use the factory pattern for client creation:
```python
from src.kortana.llm_clients.factory import create_llm_client

client = create_llm_client(provider="openai", model="gpt-4")
response = await client.generate(prompt)
```

## Testing

### Test Framework

- **Framework**: Pytest (configured in `pytest.ini`)
- **Location**: `tests/` directory with subdirectories:
  - `tests/unit/`: Unit tests for individual components
  - `tests/integration/`: Integration tests for component interactions

### Writing Tests

- **High Coverage**: Aim for >80% code coverage for new features
- **Test Structure**: Follow existing patterns
  ```python
  import pytest
  from src.kortana.modules.memory_core.services import MemoryCoreService
  
  @pytest.fixture
  def memory_service():
      """Fixture providing a test memory service."""
      return MemoryCoreService(db_session=test_db)
  
  def test_search_memories(memory_service):
      """Test semantic memory search functionality."""
      # Arrange
      test_query = "What is machine learning?"
      
      # Act
      results = memory_service.search_memories_semantic(test_query)
      
      # Assert
      assert len(results) > 0
      assert all(hasattr(r, 'content') for r in results)
  ```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_memory_core.py

# Run with coverage
pytest --cov=src/kortana --cov-report=html

# Run specific test
pytest tests/unit/test_memory_core.py::test_search_memories -v
```

### Test Requirements

- Write unit tests for all new functions and classes
- Write integration tests for multi-component features
- Mock external dependencies (APIs, databases) in unit tests
- Use real dependencies in integration tests (with test databases)
- Test both happy paths and error cases
- Include edge cases and boundary conditions

## Documentation

### Documentation Structure

All documentation lives in `/docs`:

- `ARCHITECTURE.md`: System architecture overview
- `API_ENDPOINTS.md`: API documentation
- `SECURITY_MODULE.md`: Security features guide
- `MEMORY_CORE.md`: Memory system details
- `GETTING_STARTED.md`: Setup and installation guide
- `NEW_FEATURES.md`: Feature documentation
- Feature-specific docs for major components

### Documentation Standards

When adding new features:

1. **Update existing docs**: Add your feature to relevant existing documentation
2. **Create feature docs**: For major features, create dedicated documentation
3. **Include examples**: Provide code examples and usage patterns
4. **Update README**: Add high-level overview to main README.md
5. **API docs**: Document new endpoints in API_ENDPOINTS.md

Documentation format:
```markdown
# Feature Name

## Overview
Brief description of what the feature does.

## Usage
Code examples showing how to use the feature.

## API Reference
Detailed parameter and return value documentation.

## Examples
Real-world usage scenarios.
```

## Git Practices

### Commit Messages

Follow **Conventional Commits** specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(memory): add vector similarity search with Pinecone

fix(security): resolve SQL injection vulnerability in query handler

docs(readme): update installation instructions for Python 3.11

test(core): add integration tests for orchestrator pipeline

refactor(llm): extract common client logic to base class
```

### Pull Request Guidelines

1. **Branch naming**: `feature/description`, `fix/description`, `docs/description`
2. **Small PRs**: Keep changes focused and reviewable
3. **Description**: Clearly describe what and why
4. **Link issues**: Reference related issues with `Fixes #123`
5. **Tests**: Include tests for new functionality
6. **Documentation**: Update relevant docs

### Code Review Focus

When reviewing code, prioritize:
1. **Security**: Check for vulnerabilities and secrets
2. **Ethical alignment**: Ensure changes align with Trinity principles
3. **Type safety**: Verify type hints are correct
4. **Test coverage**: Ensure adequate testing
5. **Documentation**: Check for updated docs

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/madouble7/kortana.git
cd kortana

# Create virtual environment
python -m venv venv311
source venv311/bin/activate  # Linux/Mac
# or: venv311\Scripts\activate.bat  # Windows

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Initialize database
alembic upgrade head

# Run tests
pytest
```

### Development Cycle

1. **Create feature branch**: `git checkout -b feature/my-feature`
2. **Implement changes**: Follow coding standards above
3. **Add tests**: Write comprehensive tests
4. **Run linters**: `ruff check . && mypy src/`
5. **Run tests**: `pytest`
6. **Update docs**: Add/update relevant documentation
7. **Commit changes**: Use conventional commit messages
8. **Push and create PR**: Follow PR guidelines

## AI-Specific Guidelines

### When Working with LLMs

- **Prompt Engineering**: Store prompts in `src/kortana/core/prompts.py`
- **Context Management**: Be mindful of token limits
- **Error Handling**: Always handle API failures gracefully
- **Response Validation**: Validate LLM outputs before use
- **Ethical Checks**: Apply ethical evaluators to all AI responses

### Memory Management

- **Relevance**: Only store meaningful interactions
- **Embeddings**: Always generate embeddings for searchability
- **Metadata**: Include rich metadata (timestamps, types, sentiments)
- **Cleanup**: Implement retention policies for old memories

### Autonomous Features

When implementing autonomous behaviors:
- Add appropriate safety checks
- Log all autonomous actions
- Provide override mechanisms
- Test thoroughly in isolated environments
- Document behavior and limitations

## Common Patterns

### Adding a New API Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from src.kortana.services.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/feature", tags=["feature"])

@router.post("/process")
async def process_request(
    data: RequestSchema,
    db: Session = Depends(get_db)
) -> ResponseSchema:
    """
    Process a request with security checks.
    
    Args:
        data: Request data matching RequestSchema
        db: Database session
        
    Returns:
        Processed response
    """
    # Validate input
    # Apply security checks
    # Process request
    # Return response
    pass
```

### Adding a New Module

```python
# src/kortana/modules/my_module/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── services.py    # Business logic
└── routers.py     # API endpoints
```

### Database Operations

```python
from sqlalchemy.orm import Session
from src.kortana.modules.memory_core.models import CoreMemory

def create_memory(db: Session, content: str, memory_type: str) -> CoreMemory:
    """Create a new memory with proper session handling."""
    memory = CoreMemory(content=content, type=memory_type)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory
```

## Additional Resources

- **Project Blueprint**: See `KOR'TANA_BLUEPRINT.md` for vision and goals
- **Architecture Details**: See `docs/ARCHITECTURE.md`
- **API Documentation**: See `docs/API_ENDPOINTS.md`
- **Security Guide**: See `docs/SECURITY_MODULE.md`
- **Getting Started**: See `docs/GETTING_STARTED.md`

## Questions?

For questions or clarifications:
1. Check existing documentation in `/docs`
2. Review similar implementations in the codebase
3. Create an issue with the `question` label
4. Tag maintainers in PR discussions

---

**Remember**: Every change should embody Wisdom, Compassion, and Truth. Code thoughtfully, test thoroughly, and document comprehensively.
