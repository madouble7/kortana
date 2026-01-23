#!/usr/bin/env python3
"""
Kor'tana Autonomous Monitor - Simple Version
Always-on monitoring system compatible with current environment
"""

import os
import sys
import time
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path

# Configure logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_monitor_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KortanaSimpleMonitor')

class SimpleAutonomousMonitor:
    def __init__(self):
        self.running = False
        self.processes = {}
        self.monitoring_threads = []
        self.base_dir = Path.cwd()
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration"""
        config = {
            'monitoring_interval': 60,
            'max_errors_before_alert': 5,
            'auto_recovery': True,
            'continuous_mode': True
        }
        return config

    def start_monitoring_process(self, script_name, args=None, continuous=False):
        """Start a monitoring process"""
        try:
            script_path = self.base_dir / script_name
            if not script_path.exists():
                logger.error(f"Script not found: {script_name}")
                return None

            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)

            logger.info(f"Starting process: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.base_dir
            )

            # Store process with metadata
            process_id = f"{script_name}_{process.pid}"
            self.processes[process_id] = {
                'process': process,
                'script': script_name,
                'start_time': datetime.now(),
                'status': 'running',
                'restart_count': 0
            }

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(process_id,),
                daemon=True
            )
            monitor_thread.start()
            self.monitoring_threads.append(monitor_thread)

            return process_id

        except Exception as e:
            logger.error(f"Failed to start {script_name}: {str(e)}")
            return None

    def _monitor_process(self, process_id):
        """Monitor a single process"""
        while self.running and process_id in self.processes:
            process_info = self.processes[process_id]
            process = process_info['process']

            # Check if process is still running
            if process.poll() is not None:
                return_code = process.poll()
                logger.warning(f"Process {process_id} exited with code {return_code}")

                # Auto-recovery
                if self.config['auto_recovery']:
                    logger.info(f"Attempting to restart {process_id}")
                    self._restart_process(process_id)
                else:
                    process_info['status'] = 'stopped'
                return

            # Read output if available
            self._read_process_output(process)

            # Sleep briefly to prevent CPU overload
            time.sleep(1)

    def _read_process_output(self, process):
        """Read and log process output"""
        try:
            # Read stdout
            if process.stdout:
                output = process.stdout.readline()
                if output:
                    logger.info(f"OUTPUT: {output.strip()}")

            # Read stderr
            if process.stderr:
                error = process.stderr.readline()
                if error:
                    logger.error(f"ERROR: {error.strip()}")
        except:
            pass  # Process may have terminated

    def _restart_process(self, process_id):
        """Restart a failed process"""
        if process_id not in self.processes:
            return

        process_info = self.processes[process_id]
        process_info['restart_count'] += 1
        max_restarts = 3

        if process_info['restart_count'] > max_restarts:
            logger.error(f"Process {process_id} failed too many times, not restarting")
            process_info['status'] = 'failed'
            return

        logger.info(f"Restarting {process_id} (attempt {process_info['restart_count']})")

        # Start new process
        script_name = process_info['script']
        new_process_id = self.start_monitoring_process(script_name)

        if new_process_id:
            # Update the process ID mapping
            self.processes[new_process_id] = self.processes.pop(process_id)
            logger.info(f"Successfully restarted {script_name} as {new_process_id}")
        else:
            logger.error(f"Failed to restart {script_name}")

    def start_available_monitoring(self):
        """Start monitoring with available scripts"""
        logger.info("Starting Kor'tana Simple Autonomous Monitor")

        # List of scripts to try (in priority order)
        scripts_to_try = [
            # Core monitoring
            'autonomous_monitor.py',
            'monitor_autonomous_activity_new.py',
            'monitor_autonomous_activity.py',

            # System health
            'file_system_monitor.py',
            'check_server.py',
            'status_check.py',

            # Development
            'code_review_analysis.py',
            'comprehensive_system_fix.py',
            'complete_autonomous_verification.py',

            # Genesis protocol
            'monitor_genesis_protocol.py',
            'check_genesis_status.py',

            # Validation
            'autonomous_validation_silent.py',
            'complete_autonomous_verification.py'
        ]

        started_processes = 0

        for script in scripts_to_try:
            if (self.base_dir / script).exists():
                process_id = self.start_monitoring_process(script)
                if process_id:
                    started_processes += 1
                    time.sleep(1)  # Stagger startup
            else:
                logger.info(f"Script not available: {script}")

        logger.info(f"Started {started_processes} monitoring processes")

        # Always start the simple directory analysis
        if (self.base_dir / 'simple_directory_analysis.py').exists():
            self.start_monitoring_process('simple_directory_analysis.py')
            started_processes += 1

        return started_processes

    def start_continuous_audit(self):
        """Start continuous code quality monitoring"""
        logger.info("Starting continuous code quality monitoring")

        # Run Ruff check periodically
        def ruff_monitor():
            while self.running:
                try:
                    logger.info("Running Ruff code quality check...")
                    result = subprocess.run(
                        ['python', '-m', 'ruff', 'check', '.', '--statistics'],
                        capture_output=True,
                        text=True,
                        cwd=self.base_dir
                    )
                    logger.info(f"Ruff check completed. Return code: {result.returncode}")

                    # Log summary if available
                    if result.stdout:
                        lines = result.stdout.split('\n')
                        for line in lines[-10:]:  # Last 10 lines
                            if line.strip():
                                logger.info(f"RUFF: {line.strip()}")

                except Exception as e:
                    logger.error(f"Ruff monitoring error: {str(e)}")

                # Sleep for 5 minutes between checks
                time.sleep(300)

        # Start Ruff monitoring thread
        ruff_thread = threading.Thread(target=ruff_monitor, daemon=True)
        ruff_thread.start()
        self.monitoring_threads.append(ruff_thread)

    def monitor_system_health(self):
        """Monitor overall system health"""
        while self.running:
            try:
                # Check process health
                active_processes = sum(1 for p in self.processes.values() if p['status'] == 'running')
                total_processes = len(self.processes)

                logger.info(f"System Health: {active_processes}/{total_processes} processes active")

                # Check for failed processes
                failed_processes = [p for p in self.processes.values() if p['status'] == 'failed']
                if failed_processes:
                    logger.warning(f"{len(failed_processes)} processes in failed state")

                # Sleep for monitoring interval
                time.sleep(self.config['monitoring_interval'])

            except Exception as e:
                logger.error(f"System health monitoring error: {str(e)}")
                time.sleep(10)

    def stop_all_processes(self):
        """Stop all monitoring processes"""
        logger.info("Stopping all monitoring processes")

        for process_id, process_info in self.processes.items():
            try:
                process = process_info['process']
                if process.poll() is None:  # Still running
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"Stopped {process_id}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"Force killed {process_id}")
            except Exception as e:
                logger.error(f"Error stopping {process_id}: {str(e)}")

        self.processes.clear()
        logger.info("All processes stopped")

    def run(self):
        """Main daemon loop"""
        try:
            self.running = True
            logger.info("Kor'tana Simple Autonomous Monitor started")

            # Start available monitoring processes
            started_count = self.start_available_monitoring()

            # Start continuous audit
            self.start_continuous_audit()

            # Start system health monitoring
            health_thread = threading.Thread(target=self.monitor_system_health, daemon=True)
            health_thread.start()

            logger.info(f"Monitoring system active with {started_count} processes")

            # Keep main thread alive
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Daemon error: {str(e)}")
        finally:
            self.stop_all_processes()
            logger.info("Kor'tana Simple Autonomous Monitor stopped")

def main():
    """Main entry point"""
    monitor = SimpleAutonomousMonitor()

    try:
        monitor.run()
    except Exception as e:
        logger.error(f"Fatal error in simple monitor: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
