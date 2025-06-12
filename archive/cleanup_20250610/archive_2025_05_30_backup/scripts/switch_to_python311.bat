@echo off
echo ===== Python 3.11 Migration Script =====

REM Check if Python 3.11 is installed
python -c "import sys; exit(0) if sys.version_info.major == 3 and sys.version_info.minor == 11 else exit(1)" 2>nul
if %errorlevel% == 0 (
    echo Python 3.11 is already installed and active!
    goto :create_venv
) else (
    echo Python 3.11 is not active. Checking if it's available...
)

REM Try to find Python 3.11 using py launcher
py -3.11 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Found Python 3.11 via py launcher.
    set PYTHON_CMD=py -3.11
    goto :create_venv
)

REM Try direct python3.11 command
python3.11 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Found Python 3.11 via direct command.
    set PYTHON_CMD=python3.11
    goto :create_venv
)

echo Python 3.11 not found. Please install it from https://www.python.org/downloads/release/python-3116/
echo After installing, run this script again.
exit /b 1

:create_venv
echo.
echo Creating new virtual environment with Python 3.11...
if exist venv311 (
    echo Warning: venv311 directory already exists! Continuing will reuse this directory.
    choice /C YN /M "Do you want to continue"
    if errorlevel 2 exit /b 0
)

if "%PYTHON_CMD%"=="" (
    py -3.11 -m venv venv311
) else (
    %PYTHON_CMD% -m venv venv311
)

if %errorlevel% neq 0 (
    echo Failed to create virtual environment!
    exit /b 1
)

echo.
echo Activating new virtual environment...
call venv311\Scripts\activate.bat
python --version

echo.
echo Installing dependencies from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Warning: Some dependencies may have failed to install.
)

echo.
echo ===== MIGRATION COMPLETE =====
echo The new Python 3.11 environment is now active and ready to use.
echo To activate this environment in future sessions, run:
echo     call venv311\Scripts\activate.bat
echo.
echo To deactivate the environment, run:
echo     deactivate
echo.
