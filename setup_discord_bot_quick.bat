@echo off
REM Kor'tana Discord Bot - Quick Setup for Windows
REM This scripts helps you complete the bot configuration

setlocal enabledelayedexpansion

title Kor'tana Discord Bot Setup

echo.
echo ============================================================================
echo  KOR'TANA DISCORD BOT - SETUP WIZARD
echo ============================================================================
echo.
echo Your Discord App is ready:
echo   Application ID: 1421497726201233418
echo   Status: Pre-configured
echo.
echo This wizard will guide you through the final setup step.
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

REM Run setup script
python setup_discord_bot_quick.py

REM Check if setup was successful
if errorlevel 0 (
    echo.
    echo Setup complete! Press any key to close.
    pause
) else (
    echo.
    echo Setup failed. Check errors above.
    pause
)
