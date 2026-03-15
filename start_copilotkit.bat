@echo off
REM Start Kor'tana with CopilotKit Frontend
REM This script starts both the backend and frontend servers

echo.
echo ============================================================
echo   Starting Kor'tana with CopilotKit Integration
echo ============================================================
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found
    if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo Please edit .env and add your API keys
    ) else (
        echo Creating default .env file...
        (
            echo # Kor'tana Configuration
            echo KORTANA_API_KEY=your_api_key_here
            echo LOG_LEVEL=INFO
            echo.
            echo # LLM Configuration
            echo OPENAI_API_KEY=your_openai_key_here
            echo ANTHROPIC_API_KEY=your_anthropic_key_here
            echo.
            echo # Database
            echo MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db
        ) > .env
        echo .env file created. Please edit it and add your API keys
    )
    echo.
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
)

echo.
echo Starting servers...
echo - Backend will be available at: http://localhost:8000
echo - Frontend will be available at: http://localhost:5173
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Start backend in a new window
echo Starting backend server...
start "Kor'tana Backend" cmd /k "python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in a new window
echo Starting frontend server...
cd frontend
start "Kor'tana Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ============================================================
echo   Kor'tana is running!
echo ============================================================
echo.
echo   Frontend: http://localhost:5173
echo   Backend API Docs: http://localhost:8000/docs
echo.
echo Close the terminal windows to stop the servers
echo.
pause
