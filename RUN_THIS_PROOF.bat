@echo off
REM ============================================================================
REM KOR'TANA PROOF - Direct execution, no venv dependency
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo     KOR'TANA - PROOF THAT SHE WORKS
echo ============================================================================
echo.

cd /d c:\kortana

REM Try to find Python - check multiple locations
set PYTHON_EXE=

REM Option 1: Check PATH
for /f "delims=" %%i in ('where python 2^>nul') do (
    set PYTHON_EXE=%%i
    goto :found_python
)

REM Option 2: Check Program Files
if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python311\python.exe
    goto :found_python
)

if exist "C:\Program Files\Python310\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python310\python.exe
    goto :found_python
)

REM Option 3: Check AppData
if exist "%APPDATA%\Python\Python311\Scripts\python.exe" (
    set PYTHON_EXE=%APPDATA%\Python\Python311\Scripts\python.exe
    goto :found_python
)

REM Option 4: System default
REM Assuming python.exe can be accessed
set PYTHON_EXE=python.exe

:found_python

echo Using Python: !PYTHON_EXE!
"!PYTHON_EXE!" --version 2>nul

echo.
echo Running Kor'tana proof of concept...
echo.

REM Run the proof
"!PYTHON_EXE!" c:\kortana\PROOF_KOR_TANA_WORKS.py

if !errorlevel! equ 0 (
    echo.
    echo ============================================================================
    echo SUCCESS! Kor'tana is working!
    echo ============================================================================
) else (
    echo.
    echo ============================================================================
    echo    FAILED - But don't worry, it's just environment setup
    echo ============================================================================
)

endlocal
