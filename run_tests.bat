@echo off
REM Direct test runner using cmd.exe
cd /d c:\kortana

REM Set Python path
set PYTHONPATH=c:\kortana\src

REM Run tests
echo.
echo ========================================
echo Running Full Test Suite
echo ========================================
echo.

.\.kortana_config_test_env\Scripts\pytest.exe tests\ -v --tb=short --color=yes

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Test run completed with exit code: %EXIT_CODE%
echo ========================================

exit /b %EXIT_CODE%
