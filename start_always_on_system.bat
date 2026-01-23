@echo off
REM Always-On System Quick Start for Windows
REM Activates environment and launches the autonomous system

echo.
echo ====================================================================
echo   KOR'TANA ALWAYS-ON AUTONOMOUS SYSTEM
echo   Starting All Monitoring and Development Services
echo ====================================================================
echo.

REM Activate Python environment
call .\.kortana_config_test_env\Scripts\Activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate Python environment
    echo Make sure you're in the Kor'tana root directory
    pause
    exit /b 1
)

echo.
echo [✓] Python environment activated
echo.

REM Verify required files exist
if not exist "autonomous_monitor_daemon.py" (
    echo ERROR: autonomous_monitor_daemon.py not found
    pause
    exit /b 1
)

if not exist "development_activity_tracker.py" (
    echo ERROR: development_activity_tracker.py not found
    pause
    exit /b 1
)

if not exist "autonomous_task_executor.py" (
    echo ERROR: autonomous_task_executor.py not found
    pause
    exit /b 1
)

if not exist "autonomous_health_reporter.py" (
    echo ERROR: autonomous_health_reporter.py not found
    pause
    exit /b 1
)

if not exist "launch_always_on_system.py" (
    echo ERROR: launch_always_on_system.py not found
    pause
    exit /b 1
)

echo [✓] All system files verified
echo.

REM Create state directory if needed
if not exist "state" mkdir state
if not exist "state\activity_logs" mkdir state\activity_logs
if not exist "state\reports" mkdir state\reports

echo [✓] State directories created
echo.

REM Check if monitoring should be continuous
echo.
echo Starting services...
echo.

REM Launch the master orchestrator with monitoring
python launch_always_on_system.py monitor

REM If script exits, show status
echo.
echo Checking final status...
python launch_always_on_system.py status
echo.

pause
