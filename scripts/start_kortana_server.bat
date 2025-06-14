@echo off
echo Starting Kor'tana FastAPI Server...
cd /d c:\project-kortana
call C:\project-kortana\venv311\Scripts\activate.bat
set PYTHONPATH=c:\project-kortana
echo Python environment activated
echo Starting uvicorn server...
python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000 --reload
pause
