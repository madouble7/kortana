@echo off
REM Enhanced Kor'tana Monitoring Control Script
REM ==========================================

setlocal enabledelayedexpansion

:menu
cls
echo ===============================================
echo   KOR'TANA ENHANCED MONITORING DASHBOARD
echo ===============================================
echo.
echo 1. Single Dashboard View
echo 2. Continuous Monitoring (5 min intervals)
echo 3. Quick Status Check
echo 4. Generate Test Data
echo 5. View Token Usage Report
echo 6. Check Rate Limits
echo 7. System Health Overview
echo 8. Start Auto-Monitoring (Background)
echo 0. Exit
echo.
set /p choice="Enter your choice (0-8): "

if "%choice%"=="1" goto dashboard
if "%choice%"=="2" goto continuous
if "%choice%"=="3" goto status
if "%choice%"=="4" goto testdata
if "%choice%"=="5" goto tokens
if "%choice%"=="6" goto limits
if "%choice%"=="7" goto health
if "%choice%"=="8" goto automonitor
if "%choice%"=="0" goto end
goto menu

:dashboard
echo.
echo [DASHBOARD] Launching enhanced monitoring dashboard...
python relays\monitor.py --dashboard
echo.
pause
goto menu

:continuous
echo.
echo [CONTINUOUS] Starting continuous monitoring (5 minute intervals)...
echo Press Ctrl+C to stop monitoring
python relays\monitor.py --loop 300
goto menu

:status
echo.
echo [STATUS] Quick system status check...
python relays\relay.py --status
echo.
pause
goto menu

:testdata
echo.
echo [TEST] Generating sample token usage data...
python relays\monitor.py --log-test
echo [TEST] Running relay summarization for real data...
python relays\relay.py --summarize
echo [TEST] Test data generated successfully!
echo.
pause
goto menu

:tokens
echo.
echo [TOKENS] Token usage analysis...
python -c "
import sys
sys.path.append('.')
from relays.monitor import KortanaEnhancedMonitor
monitor = KortanaEnhancedMonitor()
stats = monitor.get_token_usage_stats()
print('=== TOKEN USAGE REPORT ===')
print(f'Total Today: {stats[\"total_today\"]:,} tokens')
print('\nBy Stage (Last 24h):')
for stage, tokens in stats['last_24h'].items():
    print(f'  {stage}: {tokens:,} tokens')
print('\nBy Agent (Last 24h):')
for agent, tokens in stats['by_agent'].items():
    print(f'  {agent}: {tokens:,} tokens')
"
echo.
pause
goto menu

:limits
echo.
echo [LIMITS] Rate limit status check...
python -c "
import sys
sys.path.append('.')
from relays.monitor import KortanaEnhancedMonitor
monitor = KortanaEnhancedMonitor()
limits = monitor.get_rate_limit_status()
print('=== RATE LIMIT STATUS ===')
for service, data in limits.items():
    if service == 'error':
        continue
    print(f'\n{data[\"name\"]}:')
    if 'tpm_limit' in data:
        print(f'  TPM: {data[\"used_tokens\"]:,}/{data[\"tpm_limit\"]:,} ({data[\"tpm_percent\"]:.1f}%%)')
    if 'requests_limit' in data:
        print(f'  Requests: {data[\"used_requests\"]}/{data[\"requests_limit\"]} ({data[\"requests_percent\"]:.1f}%%)')
"
echo.
pause
goto menu

:health
echo.
echo [HEALTH] System health overview...
python -c "
import sys
sys.path.append('.')
from relays.monitor import KortanaEnhancedMonitor
monitor = KortanaEnhancedMonitor()
health = monitor.get_system_health()
agents = monitor.get_active_agents()
print('=== SYSTEM HEALTH OVERVIEW ===')
print(f'Status: {health[\"status\"].upper()}')
print(f'Active Agents: {len(agents)} ({\"\" if agents else \"None\"})')
if agents:
    print(f'  Agents: {\", \".join(agents)}')
print(f'Database Size: {health[\"database_size\"]:,} bytes')
print(f'Log Files: {health[\"log_files\"]}')
if health['last_activity']:
    print(f'Last Activity: {health[\"last_activity\"]}')
if health['issues']:
    print('Issues:')
    for issue in health['issues']:
        print(f'  - {issue}')
"
echo.
pause
goto menu

:automonitor
echo.
echo [AUTO] Setting up automatic monitoring...
echo.
echo This will create a Windows Task to run monitoring every 5 minutes.
echo The monitoring data will be logged to logs\monitor.log
echo.
set /p confirm="Do you want to continue? (y/n): "
if /i "%confirm%" neq "y" goto menu

echo.
echo [AUTO] Creating monitoring log script...
echo @echo off > monitor_background.bat
echo cd /d "%~dp0" >> monitor_background.bat
echo python relays\monitor.py --dashboard ^>^> logs\monitor.log 2^>^&1 >> monitor_background.bat
echo echo [%%date%% %%time%%] Monitoring cycle completed ^>^> logs\monitor.log >> monitor_background.bat

echo [AUTO] Creating Windows Task Scheduler entry...
schtasks /create /tn "KortanaMonitoring" /tr "%cd%\monitor_background.bat" /sc minute /mo 5 /f 2>nul
if !errorlevel! equ 0 (
    echo [AUTO] Task created successfully!
    echo [AUTO] Monitoring will run every 5 minutes in background
    echo [AUTO] Check logs\monitor.log for monitoring data
    echo [AUTO] Use 'schtasks /delete /tn KortanaMonitoring' to remove
) else (
    echo [AUTO] Failed to create scheduled task. Run as administrator.
    echo [AUTO] Manual monitoring available through this script.
)
echo.
pause
goto menu

:end
echo.
echo [EXIT] Monitoring session ended.
echo.
pause
exit /b 0
