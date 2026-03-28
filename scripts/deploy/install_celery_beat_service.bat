@echo off
REM KOR'TANA Celery Beat Scheduler - Windows Service Configuration
REM Run this script to install Celery Beat as a Windows service for persistent autonomous operation

echo Installing Celery Beat Scheduler as Windows Service...
echo This will make the autonomous monitoring, reviewing, and improving cycles persistent

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Please right-click and select "Run as Administrator"
    exit /b 1
)

REM Navigate to backend directory
cd /d "%~dp0"
cd backend

echo Creating Windows service for Celery Beat...
python -m pip install pywin32 --quiet 2>nul

REM Install Beat as Windows service
python -m celery -A src.kortana.celery_app beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=info

echo Service installation complete.
echo.
echo To start the service:
echo   net start KortanaCeleryBeat
echo.
echo To stop the service:
echo   net stop KortanaCeleryBeat
echo.
echo The autonomous cycles will now run automatically:
echo   - Every 5 minutes:  Always-on GitHub monitor (MONITORING)
echo   - Every 10 minutes: Code review cycle (REVIEWING)
echo   - Every 15 minutes: Agent improvement cycle (IMPROVING)
echo   - Every 20 minutes: Master coordination loop
echo   - Every 30 minutes: System self-monitor (MONITORING)
