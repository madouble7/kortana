@echo off
REM Quick start script for Kor'tana with Open WebUI (Windows)

echo Starting Kor'tana with Open WebUI...

REM Check if .env exists
if not exist .env (
    echo .env file not found. Creating from template...
    copy .env.template .env
    echo Please edit .env file with your API keys before continuing.
    pause
    exit /b 1
)

REM Start Kor'tana backend (use 127.0.0.1 for security, or set HOST env var for production)
if "%HOST%"=="" set HOST=127.0.0.1
echo Starting Kor'tana backend on %HOST%:8000...
start "Kor'tana Backend" cmd /k "python -m uvicorn src.kortana.main:app --host %HOST% --port 8000"

REM Wait for backend to be ready
echo Waiting for backend to be ready...
timeout /t 5 /nobreak > nul

REM Check if backend is running
curl -s http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    echo Backend failed to start. Check the backend window for errors.
    pause
    exit /b 1
)

echo Backend is ready!

REM Start Open WebUI
echo Starting Open WebUI...
docker compose -f docker-compose.openwebui.yml up -d

echo.
echo Kor'tana with Open WebUI is ready!
echo.
echo Open WebUI:    http://localhost:3000
echo API Docs:      http://localhost:8000/docs
echo Health Check:  http://localhost:8000/health
echo.
echo Documentation: docs\OPENWEBUI_INTEGRATION.md
echo.
echo To stop all services, run: scripts\stop_openwebui.bat
pause
