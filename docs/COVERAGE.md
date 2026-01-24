# Code Coverage Guide for Kor'tana

This document describes the code coverage setup and how to use it.

## Overview

Kor'tana uses `pytest-cov` to measure test coverage across the codebase. The coverage configuration is optimized to focus on critical modules like security and core functionality.

## Running Coverage Locally

### Quick Start

```bash
# Run all tests with coverage
pytest

# Or use the helper script
python scripts/run_coverage.py

# Run coverage for specific modules
pytest tests/test_security_module.py --cov=src/kortana/modules/security

# Run coverage with specific test directory
pytest tests/unit/ --cov=src
```

### View Coverage Reports

After running tests, coverage reports are generated in multiple formats:

1. **Terminal Output**: Shows missing lines directly in the console
2. **HTML Report**: Open `htmlcov/index.html` in a browser for detailed interactive report
3. **XML Report**: `coverage.xml` for CI/CD integration

```bash
# View HTML report (macOS)
open htmlcov/index.html

# View HTML report (Linux)
xdg-open htmlcov/index.html
```

## Coverage Configuration

### pytest.ini

The main pytest configuration includes:
- Coverage for `src/` directory
- Multiple report formats (terminal, HTML, XML)
- Minimum coverage threshold: 70%
- Verbose output enabled

### .coveragerc

Additional coverage settings:
- Excluded patterns (tests, archives, examples)
- Special handling for critical modules
- Custom exclusion rules for code that doesn't need coverage

## Critical Modules

The following modules are considered critical and should maintain higher coverage:

### Security Module (Target: 90%+)
- `src/kortana/modules/security/`
- Includes authentication, authorization, encryption

### Core Functionality (Target: 85%+)
- `src/kortana/core/`
- `src/kortana/brain.py`
- `src/kortana/model_router.py`

## CI/CD Integration

Coverage is automatically run in CI pipelines:

1. **GitHub Actions**: 
   - Runs on every push and pull request
   - Tests across Python 3.9, 3.10, and 3.11
   - Uploads coverage to Codecov
   - Generates coverage badge

2. **Codecov Integration**:
   - View detailed reports at codecov.io
   - Coverage trends over time
   - PR comments with coverage changes

## Coverage Targets

- **Overall Project**: 70% minimum
- **Security Module**: 90% target
- **Core Module**: 85% target
- **New Code**: Should aim for 80%+ coverage

## Best Practices

1. **Write tests first**: Follow TDD when possible
2. **Test edge cases**: Don't just aim for coverage numbers
3. **Review coverage reports**: Identify untested critical paths
4. **Update tests with code**: Keep tests in sync with implementation
5. **Don't game the system**: Focus on meaningful test coverage

## Excluding Code from Coverage

Use these patterns to exclude code that shouldn't be covered:

```python
# Pragma comment
if DEBUG:  # pragma: no cover
    print("Debug info")

# Abstract methods are automatically excluded
@abstractmethod
def method(self):
    ...

# Main blocks are excluded
if __name__ == "__main__":
    main()
```

## Troubleshooting

### Coverage not showing any results

Check that:
1. pytest-cov is installed: `pip install pytest-cov`
2. You're running from the project root
3. The `src/` directory exists

### Low coverage warnings

If coverage falls below 70%, the test suite will fail. To address:
1. Review the coverage report: `open htmlcov/index.html`
2. Identify untested code paths
3. Add appropriate tests
4. Re-run: `pytest`

### Excluding files from coverage

Edit `.coveragerc` and add patterns to the `omit` section:

```ini
[run]
omit = 
    */tests/*
    */your_excluded_file.py
```

## Additional Resources

- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Codecov documentation](https://docs.codecov.io/)
