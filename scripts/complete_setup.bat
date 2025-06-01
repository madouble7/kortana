@echo off
REM Kor'tana Autonomous System - Complete Setup & Demo
REM =================================================

echo.
echo ==========================================
echo  KOR'TANA AUTONOMOUS SYSTEM - FINAL SETUP
echo ==========================================
echo.

echo Step 1: Activating virtual environment...
call venv311\Scripts\activate.bat

echo.
echo Step 2: Installing missing packages...
pip install tiktoken google-generativeai

echo.
echo Step 3: Initializing database (if needed)...
if not exist "kortana.db" (
    echo Database not found, initializing...
    python init_db.py
) else (
    echo Database already exists
)

echo.
echo Step 4: Testing relay system...
python relays\relay.py --status

echo.
echo Step 5: Running single relay cycle...
python relays\relay.py

echo.
echo ==========================================
echo  AUTONOMOUS SYSTEM READY!
echo ==========================================
echo.
echo AUTOMATION LEVELS AVAILABLE:
echo.
echo [1] MANUAL - Full control (good for development)
echo     Commands: python relays\relay.py --status
echo               python relays\relay.py
echo               python relays\handoff.py --status
echo.
echo [2] SEMI-AUTO - Scheduled automation (recommended)
echo     Run: relays\run_relay.bat    (every 5 minutes)
echo          relays\handoff.bat      (every 10 minutes)
echo.
echo [3] HANDS-OFF - Full autonomy with Windows Task Scheduler
echo     Setup: python setup_automation.py --level hands-off
echo.
echo OPTIONAL: Set GEMINI_API_KEY for AI summarization
echo   set GEMINI_API_KEY=your_api_key_here
echo.
echo Current system status:
python relays\relay.py --status

echo.
echo Setup complete! Choose your automation level and start the system.
pause
