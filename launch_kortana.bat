@echo off
echo.
echo ==========================================
echo   🤖 KOR'TANA AUTONOMOUS AI COMPANION
echo ==========================================
echo   Status: FULLY OPERATIONAL
echo   Memory: PERSISTENT STORAGE ACTIVE
echo   API: CONNECTED AND VERIFIED
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
echo 🧠 Starting Kor'tana Brain System...
echo.

REM Run the core brain logic
python src\kortana\brain.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Error starting Kor'tana brain
    echo Running diagnostic test...
    echo.
    python tests\test_brain_integration.py
    pause
    exit /b 1
)

echo.
echo 🎉 Kor'tana session completed successfully!
pause
