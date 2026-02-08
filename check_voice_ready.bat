@echo off
REM Check if voice output requirements are met

echo.
echo ============================================================================
echo     KOR'TANA VOICE OUTPUT - REQUIREMENTS CHECK
echo ============================================================================
echo.

REM Check if in venv
python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>nul
if errorlevel 1 (
    echo [X] NOT in virtual environment
    echo     Fix: discord_bot_env\Scripts\activate
    set HAS_VENV=0
) else (
    echo [OK] Virtual environment active
    set HAS_VENV=1
)

echo.

REM Check PyNaCl
python -c "import nacl" 2>nul
if errorlevel 1 (
    echo [X] PyNaCl NOT installed
    echo     Fix: pip install PyNaCl
    set HAS_NACL=0
) else (
    echo [OK] PyNaCl installed
    set HAS_NACL=1
)

echo.

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [X] FFmpeg NOT found
    echo     Fix: Install from https://ffmpeg.org/
    set HAS_FFMPEG=0
) else (
    echo [OK] FFmpeg installed
    set HAS_FFMPEG=1
)

echo.

REM Check discord.py
python -c "import discord" 2>nul
if errorlevel 1 (
    echo [X] discord.py NOT installed
    echo     Fix: pip install discord.py
    set HAS_DISCORD=0
) else (
    echo [OK] discord.py installed
    set HAS_DISCORD=1
)

echo.
echo ============================================================================

if %HAS_VENV%==1 if %HAS_NACL%==1 if %HAS_FFMPEG%==1 if %HAS_DISCORD%==1 (
    echo.
    echo [SUCCESS] All requirements met! Voice output ready.
    echo.
    echo Run: python kortana_discord_full.py
    echo.
) else (
    echo.
    echo [WARNING] Some requirements missing. See fixes above.
    echo.
    echo Quick setup:
    echo   1. discord_bot_env\Scripts\activate
    echo   2. pip install PyNaCl discord.py
    echo   3. Install FFmpeg from https://ffmpeg.org/
    echo.
)

echo ============================================================================
echo.
pause
