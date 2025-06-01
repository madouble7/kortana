@echo off
REM Environment Variable Loader for Project Kor'tana
REM Loads .env file and starts VS Code with proper environment

echo 🚀 Loading Project Kor'tana environment...

REM Set working directory
cd /d "c:\kortana"

REM Load environment variables from .env file
if exist ".env" (
    echo ✅ Found .env file, loading variables...
    for /f "usebackq tokens=1,2 delims==" %%G in (".env") do (
        if not "%%G"=="" if not "%%G"=="REM" if not "%%G"=="//" (
            set "%%G=%%H"
            echo    Loaded: %%G
        )
    )
) else (
    echo ❌ .env file not found!
    pause
    exit /b 1
)

REM Set additional environment variables for development
set "PYTHONPATH=c:\kortana\src;c:\kortana\kortana.core;c:\kortana\kortana.team;c:\kortana\kortana.network"
set "PYTHONUNBUFFERED=1"
set "ENVIRONMENT=development"

echo ✅ Environment loaded successfully!
echo 🔧 PYTHONPATH: %PYTHONPATH%
echo 🔑 API Keys loaded: %OPENAI_API_KEY:~0,8%...

REM Start VS Code with environment
echo 🌟 Starting VS Code with loaded environment...
code .

echo 📋 VS Code started. Environment variables are now available to extensions.
pause
