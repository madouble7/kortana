@echo off
echo Starting recovery process...

:: Remove any broken virtual environment
if exist venv311 (
    echo Removing existing virtual environment...
    rmdir /s /q venv311
)

:: Create fresh virtual environment
echo Creating new virtual environment...
python -m venv venv311

:: Activate and install core requirements
echo Installing core requirements...
call venv311\Scripts\activate.bat
pip install google-generativeai==0.8.5 python-dotenv==1.0.1

:: Reset PowerShell execution policy using PowerShell command
echo Resetting PowerShell execution policy...
powershell -Command "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

echo Recovery complete. Please try these steps:
echo 1. Close all PowerShell windows
echo 2. Open a new PowerShell window
echo 3. Navigate to this directory: cd c:\kortana
echo 4. Activate the environment: .\venv311\Scripts\Activate.ps1
pause
