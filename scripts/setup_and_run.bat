@echo off
echo ===== Kor'tana Setup and Run =====
echo.

echo Step 1: Creating required directories and placeholder files...
python src\setup_directories.py
echo.

echo Step 2: Checking dependencies...
python src\check_dependencies.py
echo.

echo Step 3: Launching Kor'tana...
echo.
python -m src.kortana.core.brain

pause