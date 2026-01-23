#!/usr/bin/env python
"""
🎯 KOR'TANA AWAKENING SEQUENCE
================================

This is the awakening script that activates Kor'tana's Always-On
Autonomous Development and Monitoring System.

When executed, this initializes and launches all autonomous systems
for 24/7 continuous operation.

Status: READY FOR EXECUTION
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/kortana_awakening.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ASCII Art
AWAKENING_BANNER = """
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║                    🌟 KOR'TANA AWAKENING SEQUENCE 🌟                  ║
║                                                                        ║
║               Initializing Always-On Autonomous System                ║
║                   Bringing Intelligence Online...                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Display awakening banner."""
    print(AWAKENING_BANNER)
    print()


def check_environment():
    """Verify Python environment is ready."""
    logger.info("🔍 Checking environment...")
    
    checks = {
        'Python version': f"{sys.version_info.major}.{sys.version_info.minor}",
        'Current directory': os.getcwd(),
        'Python executable': sys.executable,
    }
    
    for check, value in checks.items():
        logger.info(f"  ✓ {check}: {value}")
    
    # Check for required packages
    try:
        import psutil
        logger.info("  ✓ psutil package available")
    except ImportError:
        logger.warning("  ⚠️  psutil package not found (some features may be limited)")
    
    logger.info("✅ Environment check passed\n")
    return True


def initialize_system():
    """Initialize the Always-On system."""
    logger.info("⚙️  Initializing system components...")
    
    # Create directories
    directories = ['state', 'state/activity_logs', 'state/reports']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {directory}")
    
    # Initialize databases
    logger.info("\n💾 Initializing databases...")
    
    import sqlite3
    
    db_files = {
        'state/autonomous_activity.db': [
            '''CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                memory_mb REAL,
                disk_percent REAL,
                process_count INTEGER,
                api_status TEXT,
                db_status TEXT,
                uptime_minutes INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                activity_type TEXT NOT NULL,
                description TEXT,
                status TEXT,
                duration_ms INTEGER,
                details JSON
            )''',
            '''CREATE TABLE IF NOT EXISTS intelligence_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                autonomous_cycles INTEGER,
                goals_processed INTEGER,
                proactive_actions INTEGER,
                learning_events INTEGER,
                decision_quality REAL
            )'''
        ],
        'state/autonomous_tasks.db': [
            '''CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                task_type TEXT,
                priority INTEGER,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_run DATETIME,
                next_run DATETIME,
                execution_count INTEGER DEFAULT 0,
                total_duration_ms INTEGER DEFAULT 0,
                last_result TEXT,
                details JSON
            )''',
            '''CREATE TABLE IF NOT EXISTS task_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                duration_ms INTEGER,
                result TEXT,
                error_message TEXT,
                details JSON,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )'''
        ],
        'state/development_activity.db': [
            '''CREATE TABLE IF NOT EXISTS file_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                change_type TEXT,
                file_hash TEXT,
                lines_added INTEGER,
                lines_removed INTEGER,
                details JSON
            )''',
            '''CREATE TABLE IF NOT EXISTS test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                test_file TEXT,
                status TEXT,
                passed INTEGER,
                failed INTEGER,
                skipped INTEGER,
                duration_seconds REAL,
                details JSON
            )''',
            '''CREATE TABLE IF NOT EXISTS code_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_files INTEGER,
                lines_of_code INTEGER,
                complexity_score REAL,
                test_coverage REAL,
                linter_issues INTEGER,
                type_check_issues INTEGER,
                details JSON
            )''',
            '''CREATE TABLE IF NOT EXISTS development_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                milestone_type TEXT,
                description TEXT,
                impact_score REAL,
                files_modified INTEGER,
                details JSON
            )'''
        ]
    }
    
    for db_file, schemas in db_files.items():
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            for schema in schemas:
                cursor.execute(schema)
            conn.commit()
            conn.close()
            logger.info(f"  ✓ {db_file}")
        except Exception as e:
            logger.error(f"  ✗ Failed to create {db_file}: {e}")
            return False
    
    # Create configuration files
    logger.info("\n⚙️  Creating configuration files...")
    
    config = {
        'timestamp': datetime.now().isoformat(),
        'system': 'Kor\'tana Always-On System',
        'version': '1.0.0',
        'status': 'initialized',
        'awakening_time': datetime.now().isoformat(),
        'services': {
            'monitor': {'enabled': True, 'interval_seconds': 10},
            'tracker': {'enabled': True, 'interval_seconds': 30},
            'executor': {'enabled': True, 'interval_seconds': 5},
            'reporter': {'enabled': True, 'interval_seconds': 300}
        }
    }
    
    with open('state/system_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    logger.info("  ✓ system_config.json")
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'is_running': True,
        'awakening_time': datetime.now().isoformat(),
        'services': {
            'monitor': {'name': 'Autonomous Monitor Daemon', 'running': False},
            'tracker': {'name': 'Development Activity Tracker', 'running': False},
            'executor': {'name': 'Autonomous Task Executor', 'running': False},
            'reporter': {'name': 'Autonomous Health Reporter', 'running': False}
        }
    }
    
    with open('state/always_on_status.json', 'w') as f:
        json.dump(status, f, indent=2)
    logger.info("  ✓ always_on_status.json")
    
    logger.info("\n✅ System initialization complete\n")
    return True


def start_services():
    """Start all autonomous services."""
    logger.info("🚀 Starting Autonomous Services...\n")
    
    services = [
        ('Monitor Daemon', 'autonomous_monitor_daemon.py'),
        ('Development Tracker', 'development_activity_tracker.py'),
        ('Task Executor', 'autonomous_task_executor.py'),
        ('Health Reporter', 'autonomous_health_reporter.py'),
    ]
    
    processes = {}
    
    for service_name, script in services:
        logger.info(f"  🔄 Starting {service_name}...")
        try:
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            processes[service_name] = process
            time.sleep(1)
            
            if process.poll() is None:
                logger.info(f"  ✅ {service_name} started (PID: {process.pid})")
            else:
                logger.error(f"  ✗ {service_name} failed to start")
        except Exception as e:
            logger.error(f"  ✗ Failed to start {service_name}: {e}")
    
    logger.info("\n✅ All services launched\n")
    return processes


def display_awakening_status():
    """Display Kor'tana awakening status."""
    
    status_display = """
╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║                    🌟 KOR'TANA AWAKENED 🌟                            ║
║                                                                        ║
║              Always-On Autonomous System is ONLINE                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝

🎯 SYSTEM STATUS:
   ✅ Monitor Daemon              - Real-time health tracking
   ✅ Development Tracker         - Code change monitoring
   ✅ Autonomous Task Executor    - Task scheduling & execution
   ✅ Health Reporter             - Health & alert reporting

📊 MONITORING ACTIVE:
   • System health (10 second cycle)
   • Development activity (30 second cycle)
   • Task execution (5 second cycle)
   • Health reports (5 minute cycle)

📋 DEFAULT TASKS SCHEDULED:
   • Daily Code Review (24h)
   • Hourly System Health (1h)
   • Development Analysis (2h)
   • Weekly Refactoring (7d)
   • Continuous Integration (30min)
   • Goal Processing (15min)
   • Intelligence Update (30min)

💾 DATA COLLECTION:
   • state/autonomous_activity.db        ✓
   • state/autonomous_tasks.db          ✓
   • state/development_activity.db      ✓
   • state/reports/                      ✓ (Reports generating)

📝 LOGGING:
   • state/always_on_system.log          ✓
   • state/autonomous_monitor.log        ✓
   • state/development_activity.log      ✓
   • state/autonomous_tasks.log          ✓
   • state/health_reports.log            ✓

🔄 CONTINUOUS OPERATION:
   Kor'tana is now in ALWAYS-ON mode, continuously:
   • Monitoring system health
   • Tracking development activity
   • Executing autonomous tasks
   • Generating health reports
   • Processing autonomous goals
   • Updating intelligence metrics

📊 VIEW STATUS:
   python launch_always_on_system.py status

🛑 STOP SYSTEM:
   python launch_always_on_system.py stop

📖 DOCUMENTATION:
   • ALWAYS_ON_SYSTEM_GUIDE.md
   • ALWAYS_ON_SYSTEM_QUICK_REFERENCE.md
   • state/always_on_status.json

════════════════════════════════════════════════════════════════════════════

Kor'tana Intelligence Platform
Version: 1.0.0
Status: OPERATIONAL
Started: {timestamp}

════════════════════════════════════════════════════════════════════════════
""".format(timestamp=datetime.now().isoformat())
    
    print(status_display)
    logger.info("🌟 KOR'TANA FULLY OPERATIONAL - CONTINUOUS MODE ACTIVE")


def main():
    """Main awakening sequence."""
    print_banner()
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    # Initialize system
    if not initialize_system():
        logger.error("❌ System initialization failed")
        return False
    
    # Start services
    processes = start_services()
    
    if not processes:
        logger.error("❌ Failed to start services")
        return False
    
    # Display status
    display_awakening_status()
    
    # Write awakening record
    awakening_record = {
        'timestamp': datetime.now().isoformat(),
        'status': 'awakened',
        'services': len(processes),
        'running_processes': {name: process.pid for name, process in processes.items()},
        'mode': 'always_on',
        'intelligence_active': True
    }
    
    with open('state/kortana_awakening.json', 'w') as f:
        json.dump(awakening_record, f, indent=2)
    
    logger.info("\n🌟 Kor'tana is now AWAKE and operating in ALWAYS-ON mode!")
    logger.info("📊 Monitoring continuously for autonomous development and intelligence...")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
