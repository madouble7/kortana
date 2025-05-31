@echo off
REM Enhanced Relay Automation Script
REM ================================
REM
REM Runs the enhanced relay system with context management and Gemini integration.
REM This script handles the monitoring every 5 minutes as requested.

setlocal

REM Set your Gemini API key here or as environment variable
REM set GEMINI_API_KEY=your_gemini_api_key_here

echo.
echo ======================================
echo  KOR'TANA ENHANCED RELAY AUTOMATION
echo ======================================
echo.

REM Change to the relays directory
cd /d "%~dp0"

REM Check if relay.py exists
if not exist "relay.py" (
    echo ERROR: relay.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if GEMINI_API_KEY is set
if "%GEMINI_API_KEY%"=="" (
    echo WARNING: GEMINI_API_KEY not set - using mock summarization
    echo To enable AI summarization, set: set GEMINI_API_KEY=your_key
    echo.
)

echo Starting enhanced relay system...
echo Monitoring agents every 5 minutes
echo Press Ctrl+C to stop
echo.

REM Run the enhanced relay in loop mode with 5-minute intervals
python relay.py --loop --interval 300

echo.
echo Enhanced relay automation stopped.
pause
