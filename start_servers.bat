@echo off
echo Starting Kor'tana Backend and LobeChat Frontend...

:: Activate Python virtual environment
call venv311\Scripts\activate

:: Start the Kor'tana backend server
start cmd /k "echo Starting Kor'tana Backend on port 8000... && python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000"

:: Start the LobeChat frontend
cd lobechat-frontend
start cmd /k "echo Starting LobeChat Frontend on port 3010... && npm run dev -- --port 3010"

echo.
echo Servers are starting up...
echo Kor'tana Backend: http://localhost:8000
echo LobeChat Frontend: http://localhost:3010
echo.
echo Press CTRL+C in the respective windows to stop the servers.
