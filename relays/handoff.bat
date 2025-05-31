@echo off
REM Agent Handoff Automation Script
REM ===============================
REM
REM Monitors token usage and triggers agent handoffs automatically.
REM Equivalent to the cron job: */10 * * * * /path/to/handoff.sh

setlocal

echo.
echo =====================================
echo  KOR'TANA AGENT HANDOFF AUTOMATION
echo =====================================
echo.

REM Change to the relays directory
cd /d "%~dp0"

REM Check if handoff.py exists
if not exist "handoff.py" (
    echo ERROR: handoff.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Starting agent handoff monitoring...
echo Checking every 10 minutes for agents needing handoff
echo Context window: 128K tokens, threshold: 80% (102.4K tokens)
echo Press Ctrl+C to stop
echo.

REM Run handoff monitoring with 10-minute intervals
python handoff.py --monitor --interval 600

echo.
echo Agent handoff monitoring stopped.
pause
