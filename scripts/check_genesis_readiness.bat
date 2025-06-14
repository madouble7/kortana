@echo off
title Kor'tana Genesis Protocol - Quick Diagnostics
echo ==============================================
echo    Kor'tana Genesis Protocol - Quick Check
echo ==============================================
echo.

echo Checking Python environment...
C:\project-kortana\venv311\Scripts\python.exe --version
if %errorlevel% neq 0 (
    echo ERROR: Python virtual environment not accessible
    pause
    exit /b 1
)

echo Checking project structure...
if not exist "c:\project-kortana\src\kortana\main.py" (
    echo ERROR: FastAPI main.py not found
    pause
    exit /b 1
)

if not exist "c:\project-kortana\lobechat-frontend\package.json" (
    echo ERROR: LobeChat frontend not found
    pause
    exit /b 1
)

echo Checking port availability...
netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 8000 is already in use
)

netstat -an | findstr ":3010" >nul
if %errorlevel% equ 0 (
    echo WARNING: Port 3010 is already in use
)

echo.
echo Testing FastAPI import...
cd /d "c:\project-kortana"
set PYTHONPATH=c:\project-kortana
C:\project-kortana\venv311\Scripts\python.exe -c "from src.kortana.main import app; print('✅ FastAPI app import successful')"
if %errorlevel% neq 0 (
    echo ERROR: FastAPI import failed - check error messages above
    pause
    exit /b 1
)

echo.
echo ==============================================
echo    ✅ All checks passed!
echo    Ready to start Genesis Protocol servers
echo ==============================================
echo.
echo Next steps:
echo 1. Run start_genesis_protocol.bat
echo 2. Or manually start servers using the checklist
echo.
pause
