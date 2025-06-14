@echo off
echo 🚀 KOR'TANA TWO-TERMINAL PROTOCOL - SERVER STARTUP
echo ================================================
echo.
echo Starting Kor'tana's FastAPI server (Terminal 1 - The Office)...
echo This will allow the autonomous processor to connect and receive goals.
echo.
echo IMPORTANT: Keep this terminal open! The server must remain running.
echo To start the autonomous processor, open a SECOND terminal and run:
echo   start_autonomous_processor.bat
echo.

cd /d "c:\project-kortana"

echo Activating virtual environment...
call venv311\Scripts\activate.bat

echo Starting FastAPI server on port 8000...
echo URL: http://127.0.0.1:8000
echo API Docs: http://127.0.0.1:8000/docs
echo.

python -m uvicorn src.kortana.main:app --port 8000 --log-level info

echo.
echo ❌ Server stopped. Kor'tana's office is now closed.
pause
