# KOR'TANA - Human Only Protocol AI Agent

## Repository Overview
KOR'TANA is the most autonomous AI agent ever created. It implements a "Human Only Protocol" where the AI executes ALL automatable tasks without human approval, only presenting scaffolded steps when human action is absolutely required.

**Owner:** Matt (Primary Human)
**Architecture:** FastAPI backend with autonomous task execution
**Philosophy:** Maximum autonomy with minimal human intervention

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

## Development Guidelines

### Code Structure
```
backend/
├── human_only_protocol.py    # Core autonomy engine
├── routers/                  # API endpoints
├── models.py                 # Database models
├── config.py                 # Configuration management
├── config.py                 # configuration management
└── main.py                   # FastAPI application
```

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

1. **`human_only_protocol.py`** - Core autonomy engine with HOP decision logic
2. **`main.py`** - FastAPI application setup and router configuration
3. **`config.py`** - Configuration management and environment loading
4. **`SCAFFOLDED_HO_STEPS.md`** - Human-only task instructions for deployment
5. **`models.py`** - Database schema definitions (SQLAlchemy)
6. **`routers/`** - API endpoint implementations

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
