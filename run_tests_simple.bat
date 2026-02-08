@echo off
setlocal
cd /d c:\kortana

REM Set up environment variables
set PYTHONPATH=c:\kortana\src
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

REM Run tests with venv python directly
echo ====================================
echo Kor'tana Test Suite Execution
echo ====================================
echo Python: c:\kortana\.kortana_config_test_env\Scripts\python.exe
echo PYTHONPATH: %PYTHONPATH%
echo Working Directory: %cd%
echo ====================================
echo.

c:\kortana\.kortana_config_test_env\Scripts\python.exe -m pytest tests\ -v --tb=short

echo.
echo ====================================
echo Test execution complete
echo ====================================
