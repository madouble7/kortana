# Kor'tana Test Execution Guide

## Environment Status ✓

### Completed Setup

- ✓ Virtual environment created at `.kortana_config_test_env/`
- ✓ All dependencies installed from `requirements.txt`
- ✓ Test dependencies installed (pytest, pytest-asyncio, pytest-mock)
- ✓ 103 test files discovered in the `tests/` directory
- ✓ Package structure unified under `kortana` namespace

### Test Suite Inventory

Total Tests: 103 test files

- Core tests: test_brain.py, test_model_router.py,  test_goals.py, etc.
- Integration tests: Multiple integration test suites
- Unit tests: Comprehensive unit test coverage

## Running Tests

### Method 1: Direct Command Line (RECOMMENDED)

Open a Command Prompt (cmd.exe) in the `c:\kortana` directory and run:

```batch
set PYTHONPATH=c:\kortana\src
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests\ -v --tb=short
```

Or use the provided batch file:

```batch
c:\kortana\run_tests_minimal.bat
```

### Method 2: Using Python Directly

From PowerShell or Command Prompt in `c:\kortana`:

```powershell
$env:PYTHONPATH = "c:\kortana\src"
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"
c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests\ -v
```

### Method 3: Run Specific Test File

```bash
c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests/test_brain.py -v
```

### Method 4: Run with Coverage

```bash
c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests\ --cov=src/kortana --cov-report=html
```

## VS Code Integration

Due to terminal profile issues, tests are best run from external terminal. However, you can:

1. Install the Test Explorer UI extension
2. Configure pytest to work with Python extension's test discovery
3. Run tests via Ctrl+Shift+P → "Python: Run All Tests"

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'kortana'`:

- Ensure PYTHONPATH includes `c:\kortana\src`
- Check that `c:\kortana\src\kortana/__init__.py` exists

### Virtual Environment Issues

If pytest is not found:

```batch
c:\kortana\.kortana_config_test_env\Scripts\pip.exe install pytest pytest-asyncio pytest-mock
```

### Port/Connection Errors

Some tests may require external services (OpenAI, Google, etc.):

- Check that API keys are configured in `.env` file
- Or tests will be skipped if services unavailable

## Next Steps

1. Run the test suite using one of the methods above
2. Address any failing tests
3. Implement additional test cases as needed
4. Set up CI/CD pipeline integration

## Useful pytest Options

- `pytest tests/ -v` - Verbose output
- `pytest tests/ -x` - Stop on first failure
- `pytest tests/ -k "brain"` - Run only tests matching pattern
- `pytest tests/ --tb=short` - Short traceback format
- `pytest tests/ --collect-only` - Only discover tests, don't run
- `pytest tests/ -n auto` - Parallel execution (if pytest-xdist installed)
