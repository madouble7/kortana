@echo off
echo 🔥 LAUNCHING AUTONOMOUS KOR'TANA
echo ================================
echo This will start Kor'tana in continuous autonomous mode
echo Press Ctrl+C to stop autonomous operation
echo.

cd /d C:\project-kortana
python src\kortana\core\brain.py --autonomous

echo.
echo Autonomous Kor'tana session ended.
pause
