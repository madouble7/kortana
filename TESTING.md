# Testing Guide for Kor'tana

Complete guide to writing, running, and maintaining tests for the Kor'tana project.

---

## 🧪 Testing Framework

### Backend (Python)

- **Test Runner**: pytest
- **Coverage**: pytest-cov
- **Async Testing**: pytest-asyncio
- **Mocking**: pytest-mock
- **Min Coverage**: 80%

### Frontend (TypeScript)

- **Test Runner**: Jest (recommended for future setup)
- **Component Testing**: React Testing Library
- **Min Coverage**: 80%

---

## 📁 Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── test_main.py                   # Main app tests
│   ├── routers/
│   │   ├── test_agents.py
│   │   ├── test_autonomy.py
│   │   ├── test_gemini.py
│   │   ├── test_github.py
│   │   ├── test_knowledge.py
│   │   ├── test_memory.py
│   │   └── test_task_queue.py
│   └── utils/
│       ├── test_logger.py
│       ├── test_config.py
│       └── test_exceptions.py
```

---

## 🚀 Running Tests

### Run All Tests

```bash
make test
# or
cd backend && python -m pytest
```

### Run Specific Test File

```bash
cd backend && python -m pytest tests/routers/test_agents.py
```

### Run Specific Test Function

```bash
cd backend && python -m pytest tests/routers/test_agents.py::test_list_agents
```

### Run Tests with Verbose Output

```bash
cd backend && python -m pytest -v
```

### Run Tests with Coverage

```bash
make test-coverage
# or
cd backend && python -m pytest --cov=. --cov-report=html
```

### Watch Mode (Auto-run on changes)

```bash
cd backend && python -m pytest --watch
```

---

## ✍️ Writing Tests

### Basic Unit Test

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test that health check endpoint works"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
```

### Testing with Fixtures

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_gemini():
    """Mock Gemini API client"""
    with patch("routers.gemini.gemini_client") as mock:
        yield mock

def test_analyze_with_gemini(mock_gemini):
    """Test Gemini analysis endpoint"""
    mock_gemini.analyze.return_value = {"result": "success"}

    response = client.post(
        "/api/gemini/analyze",
        json={"text": "test"}
    )
    assert response.status_code == 200
    mock_gemini.analyze.assert_called_once()
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function"""
    result = await some_async_function()
    assert result is not None
```

### Testing Error Cases

```python
def test_validation_error():
    """Test that invalid input raises validation error"""
    response = client.post(
        "/api/agents/create",
        json={"invalid": "data"}
    )
    assert response.status_code == 422  # Unprocessable Entity
    assert "detail" in response.json()

def test_not_found():
    """Test that missing resource returns 404"""
    response = client.get("/api/agents/nonexistent-id")
    assert response.status_code == 404
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("status,expected", [
    ("active", 200),
    ("inactive", 204),
    ("error", 500),
])
def test_multiple_statuses(status, expected):
    """Test multiple scenarios"""
    response = client.get(f"/api/status/{status}")
    assert response.status_code == expected
```

---

## 📊 Coverage Report

### Generate Coverage Report

```bash
make test-coverage
cd backend && python -m pytest --cov=. --cov-report=html
```

### View Coverage Report

```bash
# Open htmlcov/index.html in browser
open backend/htmlcov/index.html  # macOS
xdg-open backend/htmlcov/index.html  # Linux
start backend/htmlcov/index.html  # Windows
```

### Coverage Standards

- **Minimum**: 80%
- **Target**: 90%
- **Ideal**: 95%+
- **Critical paths**: 100%

---

## 🧩 Common Test Patterns

### Testing Database Operations

```python
@pytest.fixture
def test_db():
    """Create test database"""
    # Setup
    db = create_test_database()
    yield db
    # Teardown
    db.cleanup()

def test_save_document(test_db):
    """Test saving document"""
    doc = {"title": "Test", "content": "Test content"}
    result = test_db.save(doc)
    assert result["id"] is not None
```

### Testing External API Calls

```python
@pytest.fixture
def mock_github_api():
    """Mock GitHub API"""
    with patch("requests.get") as mock:
        mock.return_value.json.return_value = {"repos": []}
        yield mock

def test_fetch_repos(mock_github_api):
    """Test GitHub repo fetching"""
    response = client.get("/api/github/repos/owner/repo")
    assert response.status_code == 200
    mock_github_api.assert_called_once()
```

### Testing Authentication

```python
def test_protected_endpoint_without_auth():
    """Test that protected endpoints require auth"""
    response = client.get("/api/agents/list")
    assert response.status_code == 401

def test_protected_endpoint_with_auth():
    """Test accessing protected endpoint with auth"""
    headers = {"Authorization": "Bearer valid-token"}
    response = client.get("/api/agents/list", headers=headers)
    assert response.status_code == 200
```

---

## ✅ Test Checklist

### For New Features

- [ ] Unit tests for core logic
- [ ] Integration tests for API endpoints
- [ ] Error case testing
- [ ] Boundary condition testing
- [ ] Performance testing (if applicable)

### For Bug Fixes

- [ ] Test that reproduces the bug
- [ ] Test that validates the fix
- [ ] Regression tests to prevent recurrence
- [ ] Edge case testing

### Before Submitting PR

- [ ] All tests pass locally
- [ ] Coverage maintained or improved
- [ ] No flaky tests
- [ ] Clear test names and documentation

---

## 🔍 Debugging Tests

### Run Single Test with Debugging

```bash
cd backend && python -m pytest tests/test_main.py::test_health_check -v -s
```

### Use pytest for Step-Through Debugging

```bash
cd backend && python -m pytest tests/test_main.py -v --pdb
```

### Print Debug Information

```python
def test_something():
    result = some_function()
    print(f"Result: {result}")  # Visible with -s flag
    assert result is not None
```

### Use ipdb for Interactive Debugging

```python
def test_something():
    result = some_function()
    import ipdb; ipdb.set_trace()  # Break here
    assert result is not None
```

---

## 📈 Test Metrics

### Track Over Time

```bash
# Generate and save coverage metrics
python -m pytest --cov=. --cov-report=term-missing > coverage_$(date +%Y-%m-%d).txt
```

### CI/CD Integration

Tests run automatically on:

- Pull request creation
- Push to main/staging
- Scheduled nightly runs
- Manual workflow dispatch

---

## 🚨 Common Issues & Solutions

### Tests Failing Locally but Passing in CI

- Check Python version differences
- Verify environment variables
- Check for race conditions
- Run in same environment as CI

### Flaky Tests

- Add proper timeouts
- Use mocks for external services
- Avoid sleep() in tests
- Check for race conditions

### Slow Tests

- Use mocks for external APIs
- Use fixtures to avoid setup repetition
- Consider parameterized tests
- Profile slow tests

---

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**Keep tests comprehensive, fast, and maintainable!** ✨
