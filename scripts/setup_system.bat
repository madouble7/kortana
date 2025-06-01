@echo off
REM Kor'tana Autonomous System Setup
REM ================================
REM
REM Installs required packages and initializes the system

echo.
echo ==========================================
echo  KOR'TANA AUTONOMOUS SYSTEM SETUP
echo ==========================================
echo.

echo Installing required Python packages...
pip install google-generativeai tiktoken sqlite3

echo.
echo Initializing database...
python init_db.py

echo.
echo Testing system components...
python test_autonomous_system.py

echo.
echo Running setup demo...
python setup_automation.py --demo

echo.
echo ==========================================
echo  SETUP COMPLETE!
echo ==========================================
echo.
echo Next steps:
echo 1. Set your Gemini API key: set GEMINI_API_KEY=your_key_here
echo 2. Choose automation level: python setup_automation.py --level [manual^|semi-auto^|hands-off]
echo 3. Start system: relays\run_relay.bat
echo.
pause
