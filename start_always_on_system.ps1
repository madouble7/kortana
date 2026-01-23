# Always-On System Quick Start for PowerShell
# Activates environment and launches the autonomous system

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  KOR'TANA ALWAYS-ON AUTONOMOUS SYSTEM" -ForegroundColor Green
Write-Host "  Starting All Monitoring and Development Services" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Activate Python environment
$venvPath = ".\.kortana_config_test_env\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "[✓] Python environment activated" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python environment not found at $venvPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Verify required files exist
$requiredFiles = @(
    "autonomous_monitor_daemon.py",
    "development_activity_tracker.py",
    "autonomous_task_executor.py",
    "autonomous_health_reporter.py",
    "launch_always_on_system.py"
)

foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        Write-Host "ERROR: $file not found" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[✓] All system files verified" -ForegroundColor Green
Write-Host ""

# Create state directory if needed
$directories = @("state", "state\activity_logs", "state\reports")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "[✓] State directories created" -ForegroundColor Green
Write-Host ""

# Show available options
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  python launch_always_on_system.py start    - Start all services" -ForegroundColor Gray
Write-Host "  python launch_always_on_system.py stop     - Stop all services" -ForegroundColor Gray
Write-Host "  python launch_always_on_system.py status   - Check status" -ForegroundColor Gray
Write-Host "  python launch_always_on_system.py monitor  - Start with monitoring" -ForegroundColor Gray
Write-Host ""

# Default action
Write-Host "Starting services with continuous monitoring..." -ForegroundColor Cyan
Write-Host ""

# Launch the master orchestrator
python launch_always_on_system.py monitor

# Show final status
Write-Host ""
Write-Host "Checking final status..." -ForegroundColor Yellow
Write-Host ""
python launch_always_on_system.py status

Write-Host ""
Read-Host "Press Enter to exit"
