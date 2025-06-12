@echo off
echo 🤖 Starting Kor'tana Autonomous System
echo =====================================
echo.

REM Change to project directory
cd /d "c:\project-kortana"

REM Activate virtual environment
call venv311\Scripts\activate.bat

echo 🚀 Choose your startup mode:
echo.
echo 1. FastAPI Backend Only (for development/testing)
echo 2. Full Autonomous System (hands-off operation)
echo 3. LobeChat Integration (UI + backend)
echo 4. Interactive Development Mode
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto backend_only
if "%choice%"=="2" goto autonomous_full
if "%choice%"=="3" goto lobechat_integration
if "%choice%"=="4" goto interactive_dev
if "%choice%"=="5" goto end

:backend_only
echo.
echo 🔧 Starting FastAPI Backend...
echo Visit: http://127.0.0.1:8000/docs for API documentation
echo Press Ctrl+C to stop
echo.
python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000 --reload
goto end

:autonomous_full
echo.
echo 🚀 Starting Full Autonomous System...
echo This will run continuously until Ctrl+C
echo.
python automation_control.py --level hands-off
goto end

:lobechat_integration
echo.
echo 🌐 Starting LobeChat Integration...
echo.
echo Step 1: Starting backend server...
start "Kor'tana Backend" cmd /k "python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 /nobreak >nul

echo Step 2: Starting LobeChat frontend...
cd lobechat-frontend
start "LobeChat Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ✅ Both services starting!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:3010
echo.
echo Configure LobeChat to connect to: http://localhost:8000/adapters/lobechat/chat
goto end

:interactive_dev
echo.
echo 💻 Starting Interactive Development Mode...
echo.
python src/dev_chat_simple.py
goto end

:end
echo.
echo 👋 Kor'tana startup complete!
pause
