@echo off
echo.
echo ==========================================
echo   🤖 KOR'TANA API SERVER
echo ==========================================
echo   Status: INITIALIZING
echo   Port: 8000
echo   Host: 0.0.0.0
echo ==========================================
echo.

REM Change to project directory
cd /d "c:\project-kortana"

REM Activate virtual environment
if exist "venv311\Scripts\activate.bat" (
    call venv311\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️ Virtual environment not found at venv311\Scripts\activate.bat
    echo Using system Python...
)

echo.
echo 🚀 Starting Kor'tana API Server...
echo.

REM Run the FastAPI server
python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error starting Kor'tana API server
    pause
    exit /b 1
)

echo.
echo 🎉 Server stopped successfully!
pause
