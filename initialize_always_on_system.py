"""
Initialize Always-On System
============================

This script initializes the always-on system by:
1. Creating necessary directories
2. Initializing databases
3. Creating initial configuration files
4. Validating all components
5. Running pre-flight checks

Run once before starting the system.
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_directories():
    """Create all necessary directories."""
    logger.info("📁 Creating directories...")
    
    directories = [
        'state',
        'state/activity_logs',
        'state/reports',
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {directory}")
    
    logger.info("✅ Directories created\n")


def initialize_databases():
    """Initialize SQLite databases."""
    logger.info("💾 Initializing databases...")
    
    # Monitor database
    logger.info("  Initializing autonomous_activity.db...")
    conn = sqlite3.connect('state/autonomous_activity.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_metrics (
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
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            activity_type TEXT NOT NULL,
            description TEXT,
            status TEXT,
            duration_ms INTEGER,
            details JSON
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intelligence_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            autonomous_cycles INTEGER,
            goals_processed INTEGER,
            proactive_actions INTEGER,
            learning_events INTEGER,
            decision_quality REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("  ✓ autonomous_activity.db")
    
    # Tasks database
    logger.info("  Initializing autonomous_tasks.db...")
    conn = sqlite3.connect('state/autonomous_tasks.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
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
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            duration_ms INTEGER,
            result TEXT,
            error_message TEXT,
            details JSON,
            FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("  ✓ autonomous_tasks.db")
    
    # Development database
    logger.info("  Initializing development_activity.db...")
    conn = sqlite3.connect('state/development_activity.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL,
            change_type TEXT,
            file_hash TEXT,
            lines_added INTEGER,
            lines_removed INTEGER,
            details JSON
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            test_file TEXT,
            status TEXT,
            passed INTEGER,
            failed INTEGER,
            skipped INTEGER,
            duration_seconds REAL,
            details JSON
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS code_quality_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_files INTEGER,
            lines_of_code INTEGER,
            complexity_score REAL,
            test_coverage REAL,
            linter_issues INTEGER,
            type_check_issues INTEGER,
            details JSON
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS development_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            milestone_type TEXT,
            description TEXT,
            impact_score REAL,
            files_modified INTEGER,
            details JSON
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("  ✓ development_activity.db")
    
    logger.info("✅ Databases initialized\n")


def create_initial_config():
    """Create initial configuration files."""
    logger.info("⚙️  Creating configuration files...")
    
    # System configuration
    config = {
        'timestamp': datetime.now().isoformat(),
        'system': 'Kor\'tana Autonomous Always-On System',
        'version': '1.0.0',
        'status': 'initialized',
        'services': {
            'monitor': {
                'enabled': True,
                'interval_seconds': 10
            },
            'tracker': {
                'enabled': True,
                'interval_seconds': 30,
                'watch_dirs': ['src/', 'kortana/', 'tests/']
            },
            'executor': {
                'enabled': True,
                'interval_seconds': 5,
                'max_concurrent_tasks': 3
            },
            'reporter': {
                'enabled': True,
                'interval_seconds': 300
            }
        }
    }
    
    with open('state/system_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    logger.info("  ✓ system_config.json")
    
    # Initial status
    status = {
        'timestamp': datetime.now().isoformat(),
        'is_running': False,
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
    
    logger.info("✅ Configuration created\n")


def validate_scripts():
    """Validate that all required scripts exist."""
    logger.info("🔍 Validating scripts...")
    
    required_scripts = [
        'autonomous_monitor_daemon.py',
        'development_activity_tracker.py',
        'autonomous_task_executor.py',
        'autonomous_health_reporter.py',
        'launch_always_on_system.py'
    ]
    
    all_valid = True
    for script in required_scripts:
        if os.path.exists(script):
            logger.info(f"  ✓ {script}")
        else:
            logger.error(f"  ✗ {script} NOT FOUND")
            all_valid = False
    
    if all_valid:
        logger.info("✅ All scripts present\n")
    else:
        logger.error("✗ Some scripts are missing\n")
        return False
    
    return True


def check_python_version():
    """Check Python version."""
    logger.info("🐍 Checking Python environment...")
    
    version = sys.version_info
    logger.info(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        logger.info("✅ Python version compatible\n")
        return True
    else:
        logger.error("✗ Python 3.8+ required\n")
        return False


def check_dependencies():
    """Check required Python packages."""
    logger.info("📦 Checking dependencies...")
    
    required_packages = [
        'psutil',
        'sqlite3'
    ]
    
    all_available = True
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✓ {package}")
        except ImportError:
            logger.error(f"  ✗ {package} NOT FOUND")
            all_available = False
    
    if all_available:
        logger.info("✅ All dependencies available\n")
    else:
        logger.warning("⚠️  Some dependencies missing (psutil may be required)\n")
    
    return all_available


def run_preflight_checks():
    """Run all pre-flight checks."""
    logger.info("\n" + "="*60)
    logger.info("🚀 ALWAYS-ON SYSTEM INITIALIZATION")
    logger.info("="*60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Scripts", validate_scripts),
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            logger.error(f"✗ {check_name} check failed: {e}\n")
            all_passed = False
    
    return all_passed


def main():
    """Main initialization function."""
    
    # Run pre-flight checks
    if not run_preflight_checks():
        logger.error("❌ Pre-flight checks failed!")
        logger.error("Please resolve the issues above before continuing.")
        return False
    
    # Initialize system
    logger.info("="*60)
    logger.info("⚙️  INITIALIZING SYSTEM COMPONENTS")
    logger.info("="*60 + "\n")
    
    create_directories()
    initialize_databases()
    create_initial_config()
    
    logger.info("="*60)
    logger.info("✅ INITIALIZATION COMPLETE")
    logger.info("="*60 + "\n")
    
    logger.info("Next steps:")
    logger.info("  1. Review configuration in state/system_config.json")
    logger.info("  2. Start the system: python launch_always_on_system.py start")
    logger.info("  3. Monitor status: python launch_always_on_system.py status")
    logger.info("  4. View reports: state/reports/")
    logger.info("\nFor detailed documentation, see ALWAYS_ON_SYSTEM_GUIDE.md\n")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
