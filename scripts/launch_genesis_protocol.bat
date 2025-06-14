@echo off
title Genesis Protocol - Automated Launch
color 0A
echo.
echo ██████╗ ███████╗███╗   ███╗███████╗███████╗██╗███████╗
echo ██╔════╝ ██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
echo ██║  ███╗█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
echo ██║   ██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
echo ╚██████╔╝███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
echo  ╚═════╝ ╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
echo.
echo            PROTOCOL - AUTONOMOUS LAUNCH SEQUENCE
echo ================================================================
echo.

REM Check prerequisites
echo [1/6] Checking prerequisites...
if not exist "C:\project-kortana\venv311\Scripts\python.exe" (
    echo ❌ ERROR: Virtual environment not found
    echo Please ensure venv311 is properly installed
    pause
    exit /b 1
)

if not exist "c:\project-kortana\src\kortana\main.py" (
    echo ❌ ERROR: FastAPI main.py not found
    pause
    exit /b 1
)

if not exist "c:\project-kortana\lobechat-frontend\package.json" (
    echo ❌ ERROR: LobeChat frontend not found
    pause
    exit /b 1
)

echo ✅ Prerequisites verified

REM Kill existing processes
echo [2/6] Stopping existing servers...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
echo ✅ Cleanup complete

REM Start FastAPI Backend
echo [3/6] Starting FastAPI Backend Server...
cd /d "c:\project-kortana"
start "Kortana-FastAPI-Backend" cmd /k "title Kortana Backend && C:\project-kortana\venv311\Scripts\activate.bat && set PYTHONPATH=c:\project-kortana && echo Starting Kortana Backend... && python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000 --reload"

echo ⏳ Waiting for backend initialization...
timeout /t 8 /nobreak >nul

REM Verify backend is running
:check_backend
curl -s http://127.0.0.1:8000/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Backend still starting... waiting...
    timeout /t 3 /nobreak >nul
    goto check_backend
)
echo ✅ FastAPI Backend is running

REM Start LobeChat Frontend
echo [4/6] Starting LobeChat Frontend...
cd /d "c:\project-kortana\lobechat-frontend"
start "LobeChat-Frontend" cmd /k "title LobeChat Frontend && echo Starting LobeChat Frontend... && npm run dev -- --port 3010"

echo ⏳ Waiting for frontend initialization...
timeout /t 15 /nobreak >nul
echo ✅ Frontend startup initiated

REM Start Monitor
echo [5/6] Starting Genesis Protocol Monitor...
cd /d "c:\project-kortana"
start "Genesis-Monitor" cmd /k "title Genesis Monitor && C:\project-kortana\venv311\Scripts\activate.bat && echo Starting Genesis Protocol Monitor... && python monitor_genesis_protocol.py"

timeout /t 3 /nobreak >nul
echo ✅ Monitor started

REM Launch interfaces
echo [6/6] Opening web interfaces...
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:8000/docs"
start "" "http://localhost:3010"

echo.
echo ================================================================
echo                    🚀 GENESIS PROTOCOL READY 🚀
echo ================================================================
echo.
echo 📊 Backend API:        http://127.0.0.1:8000/docs
echo 🌐 Frontend UI:        http://localhost:3010
echo 📈 Monitor:            Running in separate window
echo.
echo ================================================================
echo                      NEXT STEPS:
echo ================================================================
echo.
echo 1. Verify both interfaces are accessible in your browser
echo 2. Submit the Genesis Protocol goal:
echo    - Option A: Use Swagger UI at /goals/submit
echo    - Option B: Run submit_proving_ground_goal.py
echo.
echo 3. Monitor autonomous execution progress in real-time
echo.
echo Press any key to submit the Genesis Protocol goal automatically...
pause >nul

echo.
echo [BONUS] Submitting Genesis Protocol Goal...
C:\project-kortana\venv311\Scripts\python.exe submit_proving_ground_goal.py

echo.
echo ================================================================
echo      🎯 PHASE 3: THE PROVING GROUND IS NOW ACTIVE! 🎯
echo ================================================================
echo.
echo Kor'tana is now autonomously executing the software engineering task.
echo Monitor her progress through the Genesis Monitor window.
echo.
pause
