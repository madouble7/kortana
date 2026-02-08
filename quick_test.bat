@echo off
REM Quick fix - rebuild the venv if it's broken

echo Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

python --version

REM Try using system Python directly instead
echo.
echo Attempting to run test with system Python...
cd /d c:\kortana

REM Set path
set PYTHONPATH=c:\kortana\src

REM Run the test directly
python simple_verify.py

pause
