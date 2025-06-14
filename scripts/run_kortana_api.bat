@echo off
REM Run Kor'tana API server for LobeChat integration
echo Starting Kor'tana API server...
echo.
echo API will be available at http://localhost:8000
echo LobeChat adapter at http://localhost:8000/api/lobe/chat
echo.

REM Ensure Python environment is activated
call venv311\Scripts\activate.bat

REM Run the application
cd src
python -m uvicorn kortana.main:app --reload --port 8000 --host 0.0.0.0

echo API server stopped.
