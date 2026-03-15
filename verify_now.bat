@echo off
REM ============================================================================
REM KTOR'TANA LIVE VERIFICATION - THE QUICK WAY
REM ============================================================================

echo.
echo ============================================================================
echo     KTOR'TANA LIVE VERIFICATION - Proving It Works
echo ============================================================================
echo.

cd /d c:\kortana

REM Find Python
for /f "delims=" %%I in ('where python') do set PYTHON=%%I

if "%PYTHON%"=="" (
    echo ERROR: Python not found in PATH
    echo Install Python from python.org and add to PATH
    pause
    exit /b 1
)

echo Using Python: %PYTHON%
%PYTHON% --version

echo.
echo Running live verification...
echo.

REM Set the path for imports
set PYTHONPATH=c:\kortana\src

REM Run the verification
%PYTHON% c:\kortana\live_verification.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================================================
    echo SUCCESS! Kor'tana core is working!
    echo ============================================================================
    echo.
    echo Next steps:
    echo 1. If you want to run tests: rebuild the venv or use system Python
    echo 2. If you want to run the Discord bot: python run_bot_direct.py
    echo 3. See ACTUAL_STATUS.md for detailed fix instructions
    echo.
) else (
    echo.
    echo ============================================================================
    echo VERIFICATION FAILED
    echo ============================================================================
    echo Check the error above to see what library is missing
    echo.
)

pause
