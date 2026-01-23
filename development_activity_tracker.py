"""
Development Activity Tracker - Autonomous Code Change Monitor
==============================================================

This service monitors:
- Code file changes and commits
- Test execution results
- Autonomous improvements and refactoring
- Code quality metrics evolution
- Development velocity

Run as a background service for continuous development tracking.
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/development_activity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Path('state').mkdir(exist_ok=True)


class DevelopmentActivityTracker:
    """Tracks all autonomous development activities."""
    
    def __init__(self, watch_dirs: Optional[List[str]] = None):
        self.watch_dirs = watch_dirs or ['src/', 'kortana/', 'tests/']
        self.db_path = 'state/development_activity.db'
        self.tracked_files = {}
        self.last_check_time = datetime.now()
        self.activity_summary_path = 'state/development_summary.json'
        self.check_interval = 30  # seconds between checks
        self.is_running = False
        
        self._initialize_database()
        self._scan_initial_state()
        logger.info("🟢 Development Activity Tracker initialized")
    
    def _initialize_database(self):
        """Initialize database for tracking activities."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # File changes table
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
            
            # Test execution table
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
            
            # Code quality metrics table
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
            
            # Development milestones table
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
            logger.info("✓ Development tracker database initialized")
        except Exception as e:
            logger.error(f"✗ Database initialization failed: {e}")
    
    def _scan_initial_state(self):
        """Scan initial state of tracked directories."""
        for watch_dir in self.watch_dirs:
            if not os.path.exists(watch_dir):
                continue
            
            for root, dirs, files in os.walk(watch_dir):
                for file in files:
                    if file.endswith(('.py', '.ts', '.tsx', '.js', '.json', '.yaml', '.yml')):
                        file_path = os.path.join(root, file)
                        self.tracked_files[file_path] = self._get_file_hash(file_path)
        
        logger.info(f"📊 Initial scan: {len(self.tracked_files)} files tracked")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file contents."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _count_line_changes(self, file_path: str) -> tuple:
        """Count lines added/removed (simplified)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = len(f.readlines())
            return (lines, 0)
        except:
            return (0, 0)
    
    def log_file_change(self, file_path: str, change_type: str = "modified"):
        """Log a file change."""
        try:
            lines_added, lines_removed = self._count_line_changes(file_path)
            new_hash = self._get_file_hash(file_path)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_changes
                (file_path, change_type, file_hash, lines_added, lines_removed)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_path, change_type, new_hash, lines_added, lines_removed))
            
            conn.commit()
            conn.close()
            
            self.tracked_files[file_path] = new_hash
            logger.info(f"📝 File change logged: {file_path} ({change_type})")
        except Exception as e:
            logger.error(f"✗ Failed to log file change: {e}")
    
    def log_test_execution(self, test_file: str, status: str,
                          passed: int = 0, failed: int = 0, skipped: int = 0,
                          duration_seconds: float = 0.0, details: Optional[Dict] = None):
        """Log test execution results."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_executions
                (test_file, status, passed, failed, skipped, duration_seconds, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_file, status, passed, failed, skipped, duration_seconds,
                  json.dumps(details or {})))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Test result logged: {test_file} - "
                       f"{passed} passed, {failed} failed, {skipped} skipped")
        except Exception as e:
            logger.error(f"✗ Failed to log test execution: {e}")
    
    def record_code_quality(self, total_files: int, lines_of_code: int,
                          complexity_score: float = 0.0, test_coverage: float = 0.0,
                          linter_issues: int = 0, type_check_issues: int = 0,
                          details: Optional[Dict] = None):
        """Record code quality metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO code_quality_metrics
                (total_files, lines_of_code, complexity_score, test_coverage,
                 linter_issues, type_check_issues, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (total_files, lines_of_code, complexity_score, test_coverage,
                  linter_issues, type_check_issues, json.dumps(details or {})))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Code quality recorded: {total_files} files, "
                       f"{lines_of_code} LOC, coverage: {test_coverage:.1f}%")
        except Exception as e:
            logger.error(f"✗ Failed to record code quality: {e}")
    
    def record_milestone(self, milestone_type: str, description: str,
                        impact_score: float = 1.0, files_modified: int = 0,
                        details: Optional[Dict] = None):
        """Record a significant development milestone."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO development_milestones
                (milestone_type, description, impact_score, files_modified, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (milestone_type, description, impact_score, files_modified,
                  json.dumps(details or {})))
            
            conn.commit()
            conn.close()
            
            logger.info(f"🎯 Milestone recorded: {milestone_type} - {description}")
        except Exception as e:
            logger.error(f"✗ Failed to record milestone: {e}")
    
    def detect_changes(self) -> Dict[str, List[str]]:
        """Detect new or modified files."""
        changes = {'new': [], 'modified': [], 'deleted': []}
        current_files = set()
        
        for watch_dir in self.watch_dirs:
            if not os.path.exists(watch_dir):
                continue
            
            for root, dirs, files in os.walk(watch_dir):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]
                
                for file in files:
                    if file.endswith(('.py', '.ts', '.tsx', '.js', '.json', '.yaml', '.yml')):
                        file_path = os.path.join(root, file)
                        current_files.add(file_path)
                        
                        if file_path not in self.tracked_files:
                            changes['new'].append(file_path)
                            self.tracked_files[file_path] = self._get_file_hash(file_path)
                        else:
                            current_hash = self._get_file_hash(file_path)
                            if current_hash != self.tracked_files[file_path]:
                                changes['modified'].append(file_path)
                                self.tracked_files[file_path] = current_hash
        
        # Detect deleted files
        for file_path in list(self.tracked_files.keys()):
            if file_path not in current_files:
                changes['deleted'].append(file_path)
                del self.tracked_files[file_path]
        
        return changes
    
    def check_cycle(self):
        """Execute a single development activity check cycle."""
        try:
            changes = self.detect_changes()
            
            if changes['new']:
                logger.info(f"🆕 New files: {len(changes['new'])}")
                for file_path in changes['new'][:5]:  # Log first 5
                    self.log_file_change(file_path, "created")
            
            if changes['modified']:
                logger.info(f"✏️  Modified files: {len(changes['modified'])}")
                for file_path in changes['modified'][:5]:  # Log first 5
                    self.log_file_change(file_path, "modified")
            
            if changes['deleted']:
                logger.info(f"🗑️  Deleted files: {len(changes['deleted'])}")
        
        except Exception as e:
            logger.error(f"✗ Check cycle failed: {e}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate development activity summary."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent activities
            cursor.execute('''
                SELECT change_type, COUNT(*) FROM file_changes
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY change_type
            ''')
            file_changes_24h = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get test results
            cursor.execute('''
                SELECT status, COUNT(*), AVG(passed), AVG(failed)
                FROM test_executions
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY status
            ''')
            test_results = {row[0]: {'count': row[1], 'avg_passed': row[2], 'avg_failed': row[3]}
                           for row in cursor.fetchall()}
            
            # Get latest code quality
            cursor.execute('''
                SELECT total_files, lines_of_code, test_coverage, linter_issues
                FROM code_quality_metrics
                ORDER BY timestamp DESC LIMIT 1
            ''')
            latest_quality = cursor.fetchone()
            
            # Get milestones
            cursor.execute('''
                SELECT milestone_type, COUNT(*) FROM development_milestones
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY milestone_type
            ''')
            milestones = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'file_changes_24h': file_changes_24h,
                'test_results': test_results,
                'code_quality': {
                    'total_files': latest_quality[0] if latest_quality else 0,
                    'lines_of_code': latest_quality[1] if latest_quality else 0,
                    'test_coverage': latest_quality[2] if latest_quality else 0.0,
                    'linter_issues': latest_quality[3] if latest_quality else 0
                } if latest_quality else {},
                'milestones_7d': milestones,
                'tracked_files': len(self.tracked_files)
            }
            
            # Save summary
            with open(self.activity_summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"📊 Development summary generated")
            return summary
        except Exception as e:
            logger.error(f"✗ Failed to generate summary: {e}")
            return {}
    
    def run(self):
        """Start the development activity tracker."""
        self.is_running = True
        logger.info("🚀 Starting Development Activity Tracker")
        logger.info(f"📍 Watch directories: {self.watch_dirs}")
        logger.info(f"⏱️  Check interval: {self.check_interval} seconds")
        
        try:
            while self.is_running:
                self.check_cycle()
                
                # Generate summary every 10 minutes
                if int(time.time()) % 600 == 0:
                    self.generate_summary()
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("⏹️  Tracker interrupted by user")
        except Exception as e:
            logger.error(f"✗ Tracker error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the tracker gracefully."""
        self.is_running = False
        final_summary = self.generate_summary()
        logger.info("🛑 Development Activity Tracker shutdown")
        logger.info(f"📊 Final tracked files: {len(self.tracked_files)}")


def main():
    """Main entry point."""
    tracker = DevelopmentActivityTracker()
    tracker.run()


if __name__ == '__main__':
    main()
