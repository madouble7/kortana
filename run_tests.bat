@echo off
echo ===== Running Kor'tana Tests =====
echo.

REM Set PYTHONPATH environment variable to include the project root
set PYTHONPATH=%cd%

REM Run the tests
python scripts\run_tests.py

echo.
echo ===== Tests Complete =====
echo.

pause
