@echo off
REM Kor'tana Discord Bot Deployment Script for Windows
REM This script sets up and starts the Discord bot

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================================
echo  KOR'TANA DISCORD BOT DEPLOYMENT
echo ============================================================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo OK: Python found

REM Check virtual environment
if not exist ".kortana_config_test_env" (
    echo.
    echo Creating virtual environment...
    python -m venv .kortana_config_test_env
)

REM Activate virtual environment
call .kortana_config_test_env\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing/checking dependencies...
pip install --upgrade pip >nul 2>&1
pip install discord.py python-dotenv openai pydantic pyyaml apscheduler >nul 2>&1

if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed properly
)

REM Check for .env file
if not exist ".env" (
    echo.
    echo Creating .env file...
    (
        echo REM Kor'tana Discord Bot Configuration
        echo.
        echo REM Discord Bot Token from https://discord.com/developers/applications
        echo DISCORD_BOT_TOKEN=
        echo.
        echo REM OpenAI API Key from https://platform.openai.com/api-keys (optional^)
        echo OPENAI_API_KEY=
        echo.
        echo REM Kor'tana Settings
        echo KORTANA_MODE=default
        echo LOG_LEVEL=INFO
    ) > .env
    echo Created .env - please add your DISCORD_BOT_TOKEN
)

REM Run deployment script
echo.
echo ============================================================================
echo Running deployment checks...
echo ============================================================================
echo.

python deploy_discord_bot.py

pause
