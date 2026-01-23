#!/usr/bin/env python
"""
Always-On System Quick Reference
=================================

A quick-start guide to common commands and operations for the Always-On system.
"""

QUICK_START = """
╔════════════════════════════════════════════════════════════════╗
║           ALWAYS-ON AUTONOMOUS SYSTEM - QUICK START            ║
╚════════════════════════════════════════════════════════════════╝

FIRST TIME SETUP:
─────────────────────────────────────────────────────────────────

1. Navigate to Kor'tana root:
   cd c:\\kortana

2. Activate Python environment:
   .\.kortana_config_test_env\Scripts\Activate.ps1

3. Initialize the system:
   python initialize_always_on_system.py

4. Start the system:
   python launch_always_on_system.py monitor

   OR use startup script:
   .\start_always_on_system.ps1


COMMON COMMANDS:
─────────────────────────────────────────────────────────────────

START SYSTEM:
  python launch_always_on_system.py start
  python launch_always_on_system.py monitor    # with monitoring

CHECK STATUS:
  python launch_always_on_system.py status

STOP SYSTEM:
  python launch_always_on_system.py stop

RESTART SYSTEM:
  python launch_always_on_system.py restart

MANAGE SPECIFIC SERVICE:
  # Start monitor daemon only
  python launch_always_on_system.py start --service monitor
  
  # Stop task executor only
  python launch_always_on_system.py stop --service executor


MONITOR & LOGS:
─────────────────────────────────────────────────────────────────

View main system log (real-time):
  Get-Content -Path state\\always_on_system.log -Wait

View monitor daemon log:
  Get-Content -Path state\\autonomous_monitor.log -Wait

View development tracker log:
  Get-Content -Path state\\development_activity.log -Wait

View task executor log:
  Get-Content -Path state\\autonomous_tasks.log -Wait

View health reporter log:
  Get-Content -Path state\\health_reports.log -Wait

List all reports:
  dir state\\reports\\


DATABASE QUERIES:
─────────────────────────────────────────────────────────────────

Health metrics (last 10 entries):
  sqlite3 state/autonomous_activity.db "SELECT * FROM health_metrics LIMIT 10;"

Recent activities:
  sqlite3 state/autonomous_activity.db "SELECT * FROM activities ORDER BY timestamp DESC LIMIT 20;"

Task executions:
  sqlite3 state/autonomous_tasks.db "SELECT * FROM task_executions ORDER BY timestamp DESC LIMIT 20;"

File changes:
  sqlite3 state/development_activity.db "SELECT * FROM file_changes ORDER BY timestamp DESC LIMIT 20;"

Test results:
  sqlite3 state/development_activity.db "SELECT * FROM test_executions ORDER BY timestamp DESC LIMIT 10;"


JSON STATUS FILES:
─────────────────────────────────────────────────────────────────

View system status:
  type state\\always_on_status.json

View development summary:
  type state\\development_summary.json

View health snapshot:
  type state\\health_status.json

Pretty print JSON (PowerShell):
  Get-Content state\\always_on_status.json | ConvertFrom-Json | ConvertTo-Json -Depth 10


SYSTEM DIAGNOSTICS:
─────────────────────────────────────────────────────────────────

Check Python environment:
  python --version
  python -c "import psutil; print('psutil OK')"

Check required files:
  dir autonomous*.py launch_always_on_system.py

Verify databases:
  dir state\\*.db

Check disk usage:
  dir C:\\ | where {$_.Name -eq 'kortana'}

List Python processes:
  tasklist | findstr python


TROUBLESHOOTING:
─────────────────────────────────────────────────────────────────

Service won't start?
  1. Check Python environment: python --version
  2. Review log: type state\\always_on_system.log
  3. Run diagnostics: python initialize_always_on_system.py
  4. Check if scripts exist: dir autonomous*.py

High resource usage?
  1. Check status: python launch_always_on_system.py status
  2. Check process list: tasklist /V | findstr python
  3. Increase monitoring intervals in service files
  4. Reduce concurrent tasks in executor

Database errors?
  1. Check database exists: dir state\\*.db
  2. Test access: sqlite3 state\\autonomous_activity.db "SELECT 1;"
  3. Check permissions: icacls state
  4. Ensure disk space: dir C:\\


PERFORMANCE OPTIMIZATION:
─────────────────────────────────────────────────────────────────

Reduce monitor frequency:
  Edit autonomous_monitor_daemon.py:
  self.monitor_interval = 10  # Change to higher value

Reduce tracker frequency:
  Edit development_activity_tracker.py:
  self.check_interval = 30    # Change to higher value

Reduce reporter frequency:
  Edit autonomous_health_reporter.py:
  self.report_interval = 300  # Change to higher value

Limit concurrent tasks:
  Edit autonomous_task_executor.py:
  for task in ready_tasks[:3]:  # Change to lower number


CONFIGURATION:
─────────────────────────────────────────────────────────────────

Edit system configuration:
  state\\system_config.json

View current status:
  state\\always_on_status.json

Add custom task:
  Edit autonomous_task_executor.py _register_default_tasks()

Configure alerts:
  Edit autonomous_health_reporter.py _check_alerts()


USEFUL SHORTCUTS:
─────────────────────────────────────────────────────────────────

# Quick status and log check
python launch_always_on_system.py status; Get-Content state\\always_on_system.log -Tail 20

# Restart and verify
python launch_always_on_system.py restart; Start-Sleep 3; python launch_always_on_system.py status

# Kill all Python processes (careful!)
Stop-Process -Name python -Force

# Create diagnostic bundle
mkdir diagnostics
Copy-Item state\\*.json diagnostics\\
Copy-Item state\\*.log diagnostics\\
sqlite3 state/autonomous_activity.db ".dump" > diagnostics\\activity_db.sql


DOCUMENTATION:
─────────────────────────────────────────────────────────────────

Main documentation:
  ALWAYS_ON_SYSTEM_GUIDE.md

Deployment summary:
  ALWAYS_ON_SYSTEM_ACTIVATED.md
  SYSTEM_DEPLOYMENT_SUMMARY.md

Quick reference (this file):
  ALWAYS_ON_SYSTEM_QUICK_REFERENCE.md


SYSTEM COMPONENTS:
─────────────────────────────────────────────────────────────────

1. Autonomous Monitor Daemon
   - Monitors system health (CPU, memory, disk)
   - Tracks services and activities
   - File: autonomous_monitor_daemon.py

2. Development Activity Tracker
   - Detects code changes
   - Tracks test executions
   - Records milestones
   - File: development_activity_tracker.py

3. Autonomous Task Executor
   - Manages scheduled tasks
   - 7 pre-configured tasks
   - Priority-based execution
   - File: autonomous_task_executor.py

4. Autonomous Health Reporter
   - Generates health reports
   - Detects alerts
   - Creates JSON/Markdown reports
   - File: autonomous_health_reporter.py

5. Launch Always-On System
   - Master orchestrator
   - Service management
   - Status reporting
   - File: launch_always_on_system.py


DEFAULT TASKS:
─────────────────────────────────────────────────────────────────

• Daily Code Review (24h interval) - HIGH priority
• Hourly System Health (1h interval) - HIGH priority
• Development Analysis (2h interval) - MEDIUM priority
• Weekly Code Refactoring (7d interval) - MEDIUM priority
• Continuous Integration (30min interval) - HIGH priority
• Goal Processing (15min interval) - HIGH priority
• Intelligence Update (30min interval) - MEDIUM priority


ALERTS:
─────────────────────────────────────────────────────────────────

🔴 CRITICAL - System-critical issues:
   - Service down
   - API offline
   - Database offline
   - Disk >90%

🟡 WARNING - Performance issues:
   - CPU >80%
   - Memory >85%

ℹ️ INFO - Status updates


QUICK TIPS:
─────────────────────────────────────────────────────────────────

✓ Always activate environment before running commands
✓ Check status regularly: python launch_always_on_system.py status
✓ Review logs for any issues: state\\*.log
✓ Keep state\\ directory clean and backed up
✓ Never delete state\\*.db unless you want to lose data
✓ Use monitor mode for debugging: python launch_always_on_system.py monitor
✓ Configure custom tasks for your workflow
✓ Adjust intervals based on your system's resources


GETTING HELP:
─────────────────────────────────────────────────────────────────

1. Check documentation: ALWAYS_ON_SYSTEM_GUIDE.md
2. Review logs: state\\*.log
3. Run diagnostics: python initialize_always_on_system.py
4. Check database: sqlite3 state\\*.db
5. Verify configuration: state\\*.json


═════════════════════════════════════════════════════════════════
Last Updated: January 23, 2026
System: Kor'tana Autonomous Always-On System v1.0.0
Status: OPERATIONAL
═════════════════════════════════════════════════════════════════
"""

if __name__ == '__main__':
    print(QUICK_START)
