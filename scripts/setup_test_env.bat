@echo off
echo Setting up a fresh test environment for Kor'tana...

rem Create a clean test directory
set TEST_ENV=.kortana_test_env
if exist %TEST_ENV% (
    echo Removing existing test environment...
    rmdir /s /q %TEST_ENV%
)

echo Creating new test environment...
python -m venv %TEST_ENV%

echo Activating test environment...
call %TEST_ENV%\Scripts\activate

echo Installing dependencies...
pip install pyyaml pydantic python-dotenv

echo Installing package in development mode...
pip install -e .

echo Environment setup complete!
echo.
echo Running diagnostic scripts...
echo.
echo ===== ENVIRONMENT DIAGNOSTIC =====
python scripts\diagnose_environment.py > env_diagnostic.log
type env_diagnostic.log

echo.
echo ===== CONFIG LOADING TEST =====
python scripts\test_config_loading.py > config_test.log
type config_test.log

echo.
echo Diagnostic complete!
echo Results saved to env_diagnostic.log and config_test.log

rem Keep the environment active for further testing
echo.
echo Test environment is active. Run 'deactivate' when finished.
echo.
