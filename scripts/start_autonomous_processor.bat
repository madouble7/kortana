@echo off
echo 🤖 KOR'TANA TWO-TERMINAL PROTOCOL - AUTONOMOUS PROCESSOR
echo ======================================================
echo.
echo Starting Kor'tana's Autonomous Goal Processor (Terminal 2 - The Engineer)...
echo This will connect to the running server and begin autonomous work.
echo.
echo PREREQUISITE: Make sure start_server.bat is running in another terminal!
echo The server must be running for the autonomous processor to work.
echo.

cd /d "c:\project-kortana"

echo Activating virtual environment...
call venv311\Scripts\activate.bat

echo Waiting 3 seconds for you to confirm the server is running...
timeout 3 > nul

echo.
echo 🔗 Testing connection to server...
python -c "import requests; print('✅ Server is reachable!' if requests.get('http://127.0.0.1:8000/health', timeout=5).status_code == 200 else '❌ Server not responding')" 2>nul || echo ❌ Server not running! Start the server first with start_server.bat

echo.
echo 🚀 Starting Autonomous Goal Processor...
echo Watch for connection messages and goal processing!
echo.

python autonomous_goal_processor.py

echo.
echo ❌ Autonomous processor stopped.
pause
