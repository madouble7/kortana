@echo off
REM Setup Kor'tana Discord Bot with Full Voice Support
REM Run this in the discord_bot_env environment

echo.
echo ============================================================================
echo     INSTALLING KOR'TANA FULL CAPABILITIES
echo ============================================================================
echo.

REM Check if in venv
python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)"
if errorlevel 1 (
    echo WARNING: Not in a virtual environment!
    echo Please activate discord_bot_env first:
    echo.
    echo     discord_bot_env\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Installing core dependencies...
pip install discord.py[voice] python-dotenv openai pydantic pyyaml --quiet

echo.
echo Installing voice processing...
pip install PyNaCl --quiet

echo.
echo Installing Kor'tana dependencies...
pip install sqlalchemy alembic anthropic fastapi uvicorn --quiet

echo.
echo ============================================================================
echo     INSTALLATION COMPLETE
echo ============================================================================
echo.
echo To run Kor'tana with full AI + voice:
echo     python kortana_discord_full.py
echo.
echo Voice features require:
echo  - PyNaCl (installed)
echo  - FFmpeg (you'll need to install separately if not present)
echo.
pause
