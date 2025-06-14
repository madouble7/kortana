@echo off
echo ==============================================
echo      Starting Kor'tana Genesis Protocol
echo ==============================================
echo.

REM Kill any existing processes
echo Stopping any existing servers...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting FastAPI Backend Server...
echo ==============================================
cd /d "c:\project-kortana"
call "C:\project-kortana\venv311\Scripts\activate.bat"
set PYTHONPATH=c:\project-kortana

REM Start FastAPI server in background
start "Kortana-API" cmd /k "python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Starting LobeChat Frontend...
echo ==============================================
cd /d "c:\project-kortana\lobechat-frontend"

REM Start frontend server in background
start "LobeChat-Frontend" cmd /k "npm run dev -- --port 3010"

echo.
echo ==============================================
echo    Servers Starting - Please Wait...
echo ==============================================
echo FastAPI Backend: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo LobeChat Frontend: http://localhost:3010
echo ==============================================
echo.
echo Waiting for servers to fully initialize...
timeout /t 10 /nobreak >nul

echo.
echo Opening interfaces...
start "" "http://127.0.0.1:8000/docs"
start "" "http://localhost:3010"

echo.
echo ==============================================
echo   Genesis Protocol Servers are running!
echo ==============================================
pause
