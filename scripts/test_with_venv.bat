@echo off
REM Kor'tana Autonomous System Test with Virtual Environment
REM =======================================================

echo.
echo ==========================================
echo  KOR'TANA AUTONOMOUS SYSTEM TEST
echo ==========================================
echo.

echo Step 1: Activating Python virtual environment...
call venv311\Scripts\activate.bat

echo Step 2: Verifying Python installation...
echo Python location:
where python
echo.
python --version
echo.

echo Step 3: Checking required packages...
python -c "import sys; print('Python executable:', sys.executable)"
python -c "try: import sqlite3; print('✓ sqlite3 available'); except: print('✗ sqlite3 missing')"
python -c "try: import json; print('✓ json available'); except: print('✗ json missing')"
python -c "try: import pathlib; print('✓ pathlib available'); except: print('✗ pathlib missing')"

echo.
echo Step 4: Running autonomous system test...
python test_autonomous_system.py

echo.
echo Test complete! Press any key to continue...
pause > nul
