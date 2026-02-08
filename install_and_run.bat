@echo off
REM Simple Discord Bot Setup - Windows Only
REM This fixes environment and installs discord.py

echo.
echo ============================================================================
echo  KOR'TANA DISCORD BOT - DEPENDENCY INSTALLER
echo ============================================================================
echo.

REM Check if we're in the right directory
if not exist "src\discord_bot.py" (
    echo ERROR: Please run this from c:\kortana directory
    echo Current directory: %cd%
    pause
    exit /b 1
)

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo.
echo Installing discord.py...
python -m pip install --upgrade discord.py

if errorlevel 1 (
    echo.
    echo WARNING: pip install had issues, but trying to continue...
)

echo.
echo Installing other dependencies...
python -m pip install python-dotenv openai pydantic pyyaml

echo.
echo ============================================================================
echo Installation complete!
echo.
echo Starting Kor'tana Discord Bot...
echo ============================================================================
echo.

python start_discord_bot.py

pause
