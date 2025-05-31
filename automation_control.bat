@echo off
REM Kor'tana Autonomous System Control
REM ==================================

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo  KOR'TANA AUTONOMOUS SYSTEM CONTROL
echo ==========================================
echo.

echo Select automation level:
echo.
echo 1. Manual Mode - Run single cycles manually
echo 2. Semi-Auto Mode - Run with monitoring (batch scripts)
echo 3. Hands-Off Mode - Windows Task Scheduler automation
echo 4. Status Check - View current system status
echo 5. Stop All Automation
echo 6. Emergency Reset
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto manual
if "%choice%"=="2" goto semi_auto
if "%choice%"=="3" goto hands_off
if "%choice%"=="4" goto status
if "%choice%"=="5" goto stop_all
if "%choice%"=="6" goto reset
echo Invalid choice. Exiting.
goto end

:manual
echo.
echo ======================================
echo  MANUAL MODE ACTIVATED
echo ======================================
echo.
call venv311\Scripts\activate.bat
echo Available commands:
echo   python relays\relay.py                 - Single relay cycle
echo   python relays\relay.py --status        - System status
echo   python relays\relay.py --summarize     - Force summarization
echo   python relays\handoff.py               - Agent handoff check
echo.
echo Manual mode ready. Run commands as needed.
cmd
goto end

:semi_auto
echo.
echo ======================================
echo  SEMI-AUTO MODE ACTIVATED
echo ======================================
echo.
echo Starting background monitoring...
echo Press Ctrl+C to stop automation
echo.

REM Start relay process in background
start "Kor'tana Relay" relays\run_relay.bat
timeout /t 2 >nul

REM Start handoff monitoring in background
start "Kor'tana Handoff" relays\handoff.bat
timeout /t 2 >nul

echo Semi-auto mode running. Close windows to stop.
echo Check log files for activity:
echo   logs\relay.log
echo   logs\handoff.log
echo.
pause
goto end

:hands_off
echo.
echo ======================================
echo  HANDS-OFF MODE SETUP
echo ======================================
echo.

REM Setup scheduled tasks
call venv311\Scripts\activate.bat
python setup_task_scheduler.py

echo.
echo Starting scheduled tasks...
schtasks /run /tn "KorTana_Relay_5min" 2>nul
schtasks /run /tn "KorTana_Handoff_10min" 2>nul

echo.
echo Hands-off mode configured!
echo Tasks will run automatically every 5-10 minutes.
echo.
goto end

:status
echo.
echo ======================================
echo  SYSTEM STATUS CHECK
echo ======================================
echo.

call venv311\Scripts\activate.bat

echo Database Status:
if exist "kortana.db" (
    echo [OK] Database found
    python -c "import sqlite3; conn = sqlite3.connect('kortana.db'); print(f'Context packages: {conn.execute(\"SELECT COUNT(*) FROM context\").fetchone()[0]}'); print(f'Agent activities: {conn.execute(\"SELECT COUNT(*) FROM agent_activity\").fetchone()[0]}'); conn.close()"
) else (
    echo [WARNING] Database not found
)

echo.
echo Relay System Status:
python relays\relay.py --status

echo.
echo Scheduled Tasks Status:
schtasks /query /tn "KorTana_Relay_5min" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Relay task configured
) else (
    echo [INFO] Relay task not configured
)

schtasks /query /tn "KorTana_Handoff_10min" >nul 2>&1
if !errorlevel! equ 0 (
    echo [OK] Handoff task configured
) else (
    echo [INFO] Handoff task not configured
)

echo.
goto end

:stop_all
echo.
echo ======================================
echo  STOPPING ALL AUTOMATION
echo ======================================
echo.

echo Stopping scheduled tasks...
schtasks /end /tn "KorTana_Relay_5min" 2>nul
schtasks /end /tn "KorTana_Handoff_10min" 2>nul

echo Closing background processes...
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Kor'tana*" 2>nul

echo All automation stopped.
echo.
goto end

:reset
echo.
echo ======================================
echo  EMERGENCY RESET
echo ======================================
echo.

echo WARNING: This will:
echo - Stop all automation
echo - Remove scheduled tasks
echo - Clear recent log entries
echo.
set /p confirm="Are you sure? (y/n): "
if not "%confirm%"=="y" goto end

echo Performing emergency reset...

REM Stop everything
schtasks /end /tn "KorTana_Relay_5min" 2>nul
schtasks /end /tn "KorTana_Handoff_10min" 2>nul
schtasks /delete /tn "KorTana_Relay_5min" /f 2>nul
schtasks /delete /tn "KorTana_Handoff_10min" /f 2>nul

REM Clear recent logs (keep last 10 lines)
for %%f in (logs\*.log) do (
    if exist "%%f" (
        tail -10 "%%f" > "%%f.tmp" 2>nul
        if exist "%%f.tmp" (
            move "%%f.tmp" "%%f" >nul
        )
    )
)

echo Emergency reset complete.
echo System returned to manual mode.
echo.
goto end

:end
echo.
echo Automation control session ended.
pause
