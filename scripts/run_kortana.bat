@echo off
echo ===== Kor'tana: Batch 1 =====
echo.

REM Set PYTHONPATH environment variable to include the project root
set PYTHONPATH=%cd%

REM Run the setup and then the brain module
python scripts\setup_and_run_batch1.py

echo.
echo ===== Run Complete =====
echo.

pause
