@echo off
echo Starting Autonomous Kor'tana System Test...
echo.

echo Step 1: Running relay orchestrator (10 seconds)...
cd /d c:\kortana\relays
start /b python relay_agent_orchestrator.py
timeout /t 10 /nobreak > nul

echo Step 2: Checking queue files...
if exist ..\queues\claude_in.txt (
    echo ✓ claude_in.txt exists
    type ..\queues\claude_in.txt
) else (
    echo ✗ claude_in.txt not found
)

if exist ..\queues\flash_in.txt (
    echo ✓ flash_in.txt exists
    type ..\queues\flash_in.txt
) else (
    echo ✗ flash_in.txt not found
)

if exist ..\queues\weaver_in.txt (
    echo ✓ weaver_in.txt exists
    type ..\queues\weaver_in.txt
) else (
    echo ✗ weaver_in.txt not found
)

echo.
echo Step 3: Starting agent task runners...
echo Starting Claude agent...
start /b python run_claude_task.py

echo Starting Flash agent...
start /b python run_flash_task.py

echo Starting Weaver agent...
start /b python run_weaver_task.py

echo.
echo System running! Check the log files for agent responses.
echo Press any key to stop all processes...
pause > nul

echo Stopping processes...
taskkill /f /im python.exe > nul 2>&1
echo Done!
