@echo off
setlocal enabledelayedexpansion

cd /d c:\kortana

echo ======================================
echo Removing old venv if it exists...
echo ======================================
if exist ".kortana_config_test_env" (
    rmdir /s /q ".kortana_config_test_env" 2>nul
    timeout /t 2
)

echo ======================================
echo Creating fresh virtual environment...
echo ======================================
"C:\Program Files\Python311\python.exe" -m venv .kortana_config_test_env
if !errorlevel! neq 0 (
    echo ERROR: Failed to create venv
    exit /b 1
)

echo ======================================
echo Upgrading pip...
echo ======================================
call .kortana_config_test_env\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
if !errorlevel! neq 0 (
    echo ERROR: Failed to upgrade pip
    exit /b 1
)

echo ======================================
echo Installing dependencies...
echo ======================================
call .kortana_config_test_env\Scripts\pip.exe install -r requirements.txt
if !errorlevel! neq 0 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo ======================================
echo Installing test dependencies...
echo ======================================
call .kortana_config_test_env\Scripts\pip.exe install pytest pytest-asyncio pytest-mock
if !errorlevel! neq 0 (
    echo ERROR: Failed to install test dependencies
    exit /b 1
)

echo ======================================
echo Environment setup complete!
echo ======================================
