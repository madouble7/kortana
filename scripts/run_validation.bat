@echo off
echo Starting validation tests...
cd /d C:\project-kortana

echo.
echo Testing Python imports...
python test_imports_simple.py > validation_output.txt 2>&1

echo.
echo Testing pytest collection (with timeout)...
timeout 30 python -m pytest --collect-only >> validation_output.txt 2>&1

echo.
echo Validation complete! Check validation_output.txt for results.
type validation_output.txt
