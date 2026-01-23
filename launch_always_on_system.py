"""
Launch Always-On System - Master Orchestration Script
======================================================

This script orchestrates the startup of all autonomous monitoring and development systems.

It starts:
1. Autonomous Monitor Daemon - System health and activity tracking
2. Development Activity Tracker - Code change and quality monitoring
3. Autonomous Task Executor - Scheduled task management
4. Autonomous Health Reporter - Status reporting and alerting

Usage:
    python launch_always_on_system.py           # Start all services
    python launch_always_on_system.py --monitor # Start only monitor
    python launch_always_on_system.py --status  # Check service status
    python launch_always_on_system.py --stop    # Stop all services
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/always_on_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Path('state').mkdir(exist_ok=True)


class AlwaysOnSystemManager:
    """Manages the always-on autonomous system."""
    
    def __init__(self):
        self.services = {
            'monitor': {
                'name': 'Autonomous Monitor Daemon',
                'script': 'autonomous_monitor_daemon.py',
                'priority': 1,
                'description': 'System health and activity tracking'
            },
            'tracker': {
                'name': 'Development Activity Tracker',
                'script': 'development_activity_tracker.py',
                'priority': 2,
                'description': 'Code change and quality monitoring'
            },
            'executor': {
                'name': 'Autonomous Task Executor',
                'script': 'autonomous_task_executor.py',
                'priority': 3,
                'description': 'Scheduled task management'
            },
            'reporter': {
                'name': 'Autonomous Health Reporter',
                'script': 'autonomous_health_reporter.py',
                'priority': 4,
                'description': 'Status reporting and alerting'
            }
        }
        
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status_file = 'state/always_on_status.json'
        self.is_running = False
        self._load_status()
        
        logger.info("🟢 Always-On System Manager initialized")
    
    def _load_status(self):
        """Load status from file."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    self.is_running = status_data.get('is_running', False)
        except Exception as e:
            logger.warning(f"Failed to load status: {e}")
    
    def _save_status(self):
        """Save current status to file."""
        try:
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'is_running': self.is_running,
                'services': {
                    service_id: {
                        'name': service['name'],
                        'running': service_id in self.processes and self.processes[service_id].poll() is None
                    }
                    for service_id, service in self.services.items()
                }
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save status: {e}")
    
    def start_service(self, service_id: str) -> bool:
        """Start a single service."""
        service = self.services.get(service_id)
        if not service:
            logger.error(f"✗ Unknown service: {service_id}")
            return False
        
        try:
            if service_id in self.processes and self.processes[service_id].poll() is None:
                logger.info(f"ℹ️  Service already running: {service['name']}")
                return True
            
            logger.info(f"🚀 Starting {service['name']}...")
            
            # Start as subprocess
            process = subprocess.Popen(
                [sys.executable, service['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes[service_id] = process
            time.sleep(1)  # Give service time to start
            
            if process.poll() is None:
                logger.info(f"✅ Started {service['name']} (PID: {process.pid})")
                return True
            else:
                logger.error(f"✗ {service['name']} failed to start")
                return False
        
        except Exception as e:
            logger.error(f"✗ Failed to start {service['name']}: {e}")
            return False
    
    def stop_service(self, service_id: str) -> bool:
        """Stop a single service."""
        service = self.services.get(service_id)
        if not service:
            logger.error(f"✗ Unknown service: {service_id}")
            return False
        
        try:
            if service_id not in self.processes:
                logger.info(f"ℹ️  Service not running: {service['name']}")
                return True
            
            process = self.processes[service_id]
            
            if process.poll() is None:
                logger.info(f"🛑 Stopping {service['name']} (PID: {process.pid})...")
                
                # Try graceful shutdown first
                process.terminate()
                try:
                    process.wait(timeout=5)
                    logger.info(f"✅ Stopped {service['name']}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️  Forcing kill on {service['name']}")
                    process.kill()
                    process.wait()
                    logger.info(f"✅ Killed {service['name']}")
                
                del self.processes[service_id]
                return True
            else:
                logger.info(f"ℹ️  Service already stopped: {service['name']}")
                del self.processes[service_id]
                return True
        
        except Exception as e:
            logger.error(f"✗ Failed to stop {service['name']}: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all services."""
        status = {}
        
        for service_id, service in self.services.items():
            is_running = False
            pid = None
            
            if service_id in self.processes:
                process = self.processes[service_id]
                is_running = process.poll() is None
                pid = process.pid if is_running else None
            
            status[service_id] = {
                'name': service['name'],
                'running': is_running,
                'pid': pid,
                'description': service['description']
            }
        
        return status
    
    def start_all(self) -> bool:
        """Start all services."""
        logger.info("=" * 60)
        logger.info("🚀 STARTING AUTONOMOUS ALWAYS-ON SYSTEM")
        logger.info("=" * 60)
        
        # Sort services by priority
        sorted_services = sorted(self.services.items(), key=lambda x: x[1]['priority'])
        
        success = True
        for service_id, service in sorted_services:
            if not self.start_service(service_id):
                success = False
            time.sleep(2)  # Delay between service starts
        
        self.is_running = success
        self._save_status()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ All services started successfully")
        else:
            logger.error("✗ Some services failed to start")
        logger.info("=" * 60)
        
        return success
    
    def stop_all(self) -> bool:
        """Stop all services."""
        logger.info("=" * 60)
        logger.info("🛑 STOPPING AUTONOMOUS ALWAYS-ON SYSTEM")
        logger.info("=" * 60)
        
        success = True
        for service_id in list(self.processes.keys()):
            if not self.stop_service(service_id):
                success = False
            time.sleep(1)
        
        self.is_running = False
        self._save_status()
        
        logger.info("=" * 60)
        if success:
            logger.info("✅ All services stopped successfully")
        else:
            logger.error("✗ Some services failed to stop")
        logger.info("=" * 60)
        
        return success
    
    def print_status(self):
        """Print current system status."""
        status = self.get_service_status()
        
        print("\n" + "=" * 60)
        print("📊 AUTONOMOUS SYSTEM STATUS")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"System Running: {'✅ YES' if self.is_running else '❌ NO'}\n")
        
        print("Services:")
        for service_id, service_status in status.items():
            running_text = "✅ RUNNING" if service_status['running'] else "⏹️  STOPPED"
            pid_text = f" (PID: {service_status['pid']})" if service_status['pid'] else ""
            print(f"  {running_text}{pid_text}")
            print(f"    {service_status['name']}")
            print(f"    {service_status['description']}\n")
        
        running_count = sum(1 for s in status.values() if s['running'])
        print(f"Summary: {running_count}/{len(self.services)} services running")
        print("=" * 60 + "\n")
    
    def monitor_services(self, check_interval: int = 30):
        """Monitor services and restart if needed."""
        logger.info("🔍 Starting service monitoring...")
        
        try:
            while True:
                status = self.get_service_status()
                
                for service_id, service_status in status.items():
                    if not service_status['running']:
                        logger.warning(f"⚠️  Service stopped: {service_status['name']}")
                        logger.info(f"🔄 Attempting to restart {service_status['name']}...")
                        self.start_service(service_id)
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Monitor error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage Kor\'tana Autonomous Always-On System'
    )
    
    parser.add_argument(
        'action',
        nargs='?',
        default='start',
        choices=['start', 'stop', 'status', 'monitor', 'restart'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--service',
        help='Specific service to manage (monitor, tracker, executor, reporter)'
    )
    
    args = parser.parse_args()
    manager = AlwaysOnSystemManager()
    
    if args.action == 'start':
        if args.service:
            manager.start_service(args.service)
        else:
            manager.start_all()
        manager.print_status()
    
    elif args.action == 'stop':
        if args.service:
            manager.stop_service(args.service)
        else:
            manager.stop_all()
        manager.print_status()
    
    elif args.action == 'status':
        manager.print_status()
    
    elif args.action == 'monitor':
        # Start all services and monitor
        manager.start_all()
        manager.print_status()
        
        # Set up signal handler
        def signal_handler(sig, frame):
            logger.info("Shutting down...")
            manager.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start monitoring
        manager.monitor_services()
    
    elif args.action == 'restart':
        if args.service:
            manager.stop_service(args.service)
            time.sleep(1)
            manager.start_service(args.service)
        else:
            manager.stop_all()
            time.sleep(2)
            manager.start_all()
        manager.print_status()


if __name__ == '__main__':
    main()
