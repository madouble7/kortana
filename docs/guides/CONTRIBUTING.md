# Contributing to Kor'tana

Thank you for your interest in contributing to Kor'tana! This document provides guidelines for contributing to the project.

## 🎯 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Git
- Docker (optional, for containerized development)

### Local Setup

```bash
# Clone the repository
git clone https://github.com/KOR-TANA/kortana.git
cd kortana

# Install dependencies
make setup

# Create .env file
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

### Verify Setup

```bash
# Check environment
make check-env

# Test backend health
make health

# Run tests
make test
```

---

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
# Create feature branch (use descriptive names)
git checkout -b feature/description-of-feature
# Examples:
# - feature/add-authentication
# - fix/security-vulnerability
# - docs/update-api-reference
```

### 2. Make Changes

```bash
# Make your changes in the appropriate files
# Backend changes: backend/
# Frontend changes: frontend/
# Documentation: docs/

# Format your code
make format

# Check linting
make lint

# Run tests
make test

# Type check
make type-check
```

### 3. Commit Your Changes

```bash
# Commit with clear message
git commit -m "feat: add new feature description"
# or
git commit -m "fix: resolve bug description"
# or
git commit -m "docs: update documentation"

# Commit message prefixes:
# - feat: New feature
# - fix: Bug fix
# - docs: Documentation update
# - test: Add/update tests
# - refactor: Code refactoring
# - perf: Performance improvement
# - chore: Build/tooling changes
```

### 4. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/description-of-feature

# Create Pull Request on GitHub
# Fill out PR template with:
# - Description of changes
# - Related issues
# - Type of change (feature/fix/docs)
# - Testing done
# - Screenshots (if applicable)
```

---

## 🧪 Testing Requirements

### Unit Tests

- Write tests for new features
- Maintain or improve code coverage (target: 80%+)
- Run tests before committing:

```bash
make test
```

### Test File Structure

```
backend/tests/
├── __init__.py
├── test_main.py
├── routers/
│   ├── test_agents.py
│   ├── test_gemini.py
│   └── ...
└── utils/
    └── test_helpers.py
```

### Example Test

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
```

---

## 📝 Code Style & Standards

### Python

- Use Black for formatting: `make format`
- Follow PEP 8 guidelines
- Use type hints: `def function(param: str) -> Dict[str, Any]:`
- Max line length: 100 characters
- Write docstrings for all public functions:

```python
def example_function(param: str) -> str:
    """
    Brief description of what the function does.

    Args:
        param: Description of the parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    pass
```

### JavaScript/TypeScript

- Use consistent formatting (Prettier)
- Use ESLint rules
- Type all components with TypeScript
- Write JSDoc comments for components:

```typescript
/**
 * Brief description of component
 *
 * @component
 * @example
 * return (<MyComponent prop="value" />)
 */
export function MyComponent({ prop }: Props): JSX.Element {
  return <div>{prop}</div>;
}
```

### Documentation

- Keep README.md updated with changes
- Update API documentation for endpoint changes
- Add comments for complex logic
- Use clear, concise language

---

## 🔒 Security Considerations

### When Contributing Code

- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive data
- Validate all user input
- Add security tests for sensitive operations
- Review SECURITY.md for security guidelines

### When Reporting Security Issues

- **Do not** create public GitHub issues for security vulnerabilities
- Email security concerns to the maintainers
- Include detailed reproduction steps
- Allow time for patching before disclosure

---

## 📚 Documentation Standards

### For New Features

1. Update main README.md if user-facing
2. Add/update endpoint documentation
3. Add examples in docstrings
4. Create/update related guide in docs/

### For Bug Fixes

1. Update relevant documentation if behavior changed
2. Add test case demonstrating the fix
3. Reference the issue number in commit message

### For Breaking Changes

1. Document migration path for users
2. Update version number following semver
3. Create migration guide in docs/

---

## 🎨 Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No new dependencies without discussion
- [ ] Type hints are complete
- [ ] Security best practices followed
- [ ] Commit messages are clear
- [ ] No merge conflicts

### Reviewers Will Check

- [ ] Code quality and style
- [ ] Test coverage
- [ ] Security implications
- [ ] Performance impact
- [ ] Documentation accuracy
- [ ] Backward compatibility

---

## 📦 Dependency Management

### Adding New Dependencies

1. **Discuss first** - Open an issue to discuss the need
2. **Justify the choice** - Explain why this dependency is necessary
3. **Check alternatives** - Ensure no better alternatives exist
4. **Update requirements** - Add to appropriate requirements file
5. **Update docs** - Document why the dependency was added

### Updating Dependencies

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Update specific dependency
pip install --upgrade package-name

# Update requirements file
pip freeze > requirements.txt
```

---

## 🚀 Deployment Notes

### Staging Deployment

- Automatic on PR merge to `staging` branch
- Test thoroughly before merge to main

### Production Deployment

- Only merged PRs to `main` are deployed
- Requires review approval
- Automatic via GitHub Actions
- Monitor deployment health

---

## 📞 Getting Help

- **Questions?** - Start a Discussion on GitHub
- **Found a bug?** - Create an Issue with reproduction steps
- **Have an idea?** - Open a Feature Request issue
- **Security concern?** - Email maintainers privately

---

## ✨ Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

Thank you for contributing to Kor'tana! 🎉
