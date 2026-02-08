#!/usr/bin/env python3
"""
Kor'tana Autonomous Monitor - Simple Version
Always-on monitoring system compatible with current environment
"""

import logging
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import requests

# Configure logging without Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("autonomous_monitor_simple.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("KortanaSimpleMonitor")


class SimpleAutonomousMonitor:
    def __init__(self):
        self.running = False
        self.processes = {}
        self.monitoring_threads = []
        self.base_dir = Path.cwd()
        self.script_search_dirs = [
            self.base_dir,
            self.base_dir / "scripts",
            self.base_dir / "src",
        ]
        self.config = self._load_config()
        self.log_dir = self.base_dir / "logs" / "autonomous_children"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Long-running scripts that should be supervised continuously.
        self.persistent_profiles = [
            {
                "script": "monitor_agent_mesh.py",
                "requires_api": False,
                "health_url": None,
            },
            {
                "script": "file_system_monitor.py",
                "requires_api": False,
                "health_url": None,
            },
            {
                "script": "monitor_autonomous_activity.py",
                "requires_api": True,
                "health_url": "http://127.0.0.1:8000/health",
            },
            {
                "script": "monitor_autonomous_development.py",
                "requires_api": True,
                "health_url": "http://127.0.0.1:8000/health",
            },
            {
                "script": "monitor_autonomous_intelligence.py",
                "requires_api": True,
                "health_url": "http://127.0.0.1:8001/health",
            },
        ]

        # One-shot scripts that should run periodically, not be treated as daemons.
        self.periodic_profiles = [
            {
                "script": "check_server.py",
                "interval": 60,
                "requires_api": False,
                "health_url": None,
            },
            {
                "script": "status_check.py",
                "interval": 120,
                "requires_api": True,
                "health_url": "http://127.0.0.1:8000/health",
            },
            {
                "script": "autonomous_monitor.py",
                "interval": 600,
                "requires_api": False,
                "health_url": None,
            },
        ]

        self.pending_persistent_profiles = []

    def _child_env(self):
        """Build child-process environment with UTF-8 console safety on Windows."""
        env = dict(**__import__("os").environ)
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return env

    def _resolve_script_path(self, script_name):
        """Resolve a script by searching known directories."""
        for directory in self.script_search_dirs:
            candidate = directory / script_name
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    def _load_config(self):
        """Load configuration"""
        config = {
            "monitoring_interval": 60,
            "max_errors_before_alert": 5,
            "auto_recovery": True,
            "continuous_mode": True,
            "max_restarts": 3,
        }
        return config

    def _is_health_endpoint_reachable(self, health_url):
        """Check whether a required API endpoint is reachable."""
        if not health_url:
            return True

        try:
            response = requests.get(health_url, timeout=3)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _profile_can_start(self, profile):
        if not profile.get("requires_api"):
            return True
        return self._is_health_endpoint_reachable(profile.get("health_url"))

    def _stderr_log_path(self, script_name):
        safe_name = script_name.replace("/", "_").replace("\\", "_")
        return self.log_dir / f"{safe_name}.stderr.log"

    def start_monitoring_process(
        self,
        script_name,
        args=None,
        continuous=False,
        restart_count=0,
        profile_name="persistent",
    ):
        """Start a monitoring process"""
        try:
            script_path = self._resolve_script_path(script_name)
            if not script_path:
                logger.error(f"Script not found: {script_name}")
                return None

            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)

            logger.info(f"Starting process: {' '.join(cmd)}")
            stderr_path = self._stderr_log_path(script_name)
            stderr_handle = open(stderr_path, "a", encoding="utf-8", errors="replace")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=stderr_handle,
                text=True,
                cwd=self.base_dir,
                env=self._child_env(),
            )

            # Store process with metadata
            process_id = f"{script_name}_{process.pid}"
            self.processes[process_id] = {
                "process": process,
                "script": script_name,
                "args": args or [],
                "start_time": datetime.now(),
                "status": "running",
                "restart_count": restart_count,
                "profile_name": profile_name,
                "continuous": continuous,
                "failure_logged": False,
                "stderr_path": stderr_path,
                "stderr_handle": stderr_handle,
            }

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_process, args=(process_id,), daemon=True
            )
            monitor_thread.start()
            self.monitoring_threads.append(monitor_thread)

            return process_id

        except Exception as e:
            logger.error(f"Failed to start {script_name}: {str(e)}")
            return None

    def _log_failure_context(self, process_id, return_code):
        """Log a short failure context block once per process lifecycle."""
        process_info = self.processes.get(process_id)
        if not process_info or process_info.get("failure_logged"):
            return

        log_path = process_info.get("stderr_path")
        process_info["failure_logged"] = True

        if not log_path or not Path(log_path).exists():
            logger.warning(
                f"No stderr log found for {process_id} (exit code {return_code})"
            )
            return

        try:
            with open(log_path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            tail = [line.rstrip() for line in lines[-12:] if line.strip()]
            if tail:
                logger.warning(
                    f"Failure context for {process_id} (exit {return_code}) from {log_path}:"
                )
                for line in tail:
                    logger.warning(f"  STDERR: {line}")
            else:
                logger.warning(
                    f"{process_id} exited with code {return_code} and produced no stderr output"
                )
        except Exception as e:
            logger.error(f"Failed reading stderr context for {process_id}: {str(e)}")

    def _monitor_process(self, process_id):
        """Monitor a single process"""
        while self.running and process_id in self.processes:
            process_info = self.processes[process_id]
            process = process_info["process"]

            # Check if process is still running
            if process.poll() is not None:
                return_code = process.poll()
                logger.warning(f"Process {process_id} exited with code {return_code}")

                # Close handles as soon as process exits.
                stderr_handle = process_info.get("stderr_handle")
                if stderr_handle and not stderr_handle.closed:
                    stderr_handle.close()

                self._log_failure_context(process_id, return_code)

                # Auto-recovery
                if self.config["auto_recovery"] and process_info.get("continuous"):
                    logger.info(f"Attempting to restart {process_id}")
                    self._restart_process(process_id)
                else:
                    process_info["status"] = "stopped"
                return

            # Read output if available
            self._read_process_output(process)

            # Sleep briefly to prevent CPU overload
            time.sleep(1)

    def _read_process_output(self, process):
        """Read and log process output"""
        # Output is redirected to DEVNULL for daemon stability.
        return

    def _restart_process(self, process_id):
        """Restart a failed process"""
        if process_id not in self.processes:
            return

        process_info = self.processes[process_id]
        next_restart_count = process_info["restart_count"] + 1
        max_restarts = self.config["max_restarts"]

        if next_restart_count > max_restarts:
            logger.error(f"Process {process_id} failed too many times, not restarting")
            process_info["status"] = "failed"
            return

        logger.info(f"Restarting {process_id} (attempt {next_restart_count})")

        # Start new process
        script_name = process_info["script"]
        args = process_info.get("args")
        profile_name = process_info.get("profile_name", "persistent")

        # Remove old process record before replacing it.
        self.processes.pop(process_id, None)

        new_process_id = self.start_monitoring_process(
            script_name,
            args=args,
            continuous=True,
            restart_count=next_restart_count,
            profile_name=profile_name,
        )

        if new_process_id:
            logger.info(f"Successfully restarted {script_name} as {new_process_id}")
        else:
            logger.error(f"Failed to restart {script_name}")

    def start_available_monitoring(self):
        """Start monitoring with available scripts"""
        logger.info("Starting Kor'tana Simple Autonomous Monitor")

        started_processes = 0

        for profile in self.persistent_profiles:
            script = profile["script"]

            if not self._resolve_script_path(script):
                logger.info(f"Persistent script not available: {script}")
                continue

            if self._profile_can_start(profile):
                process_id = self.start_monitoring_process(
                    script,
                    continuous=True,
                    profile_name="persistent",
                )
                if process_id:
                    started_processes += 1
                    time.sleep(1)  # Stagger startup
            else:
                self.pending_persistent_profiles.append(profile)
                logger.info(
                    "Deferring %s until API health check succeeds (%s)",
                    script,
                    profile.get("health_url"),
                )

        logger.info(f"Started {started_processes} persistent monitoring processes")

        return started_processes

    def _run_periodic_script(self, profile):
        script = profile["script"]
        interval = profile["interval"]

        while self.running:
            if not self._resolve_script_path(script):
                logger.info(f"Periodic script not available: {script}")
                time.sleep(interval)
                continue

            if not self._profile_can_start(profile):
                logger.info(
                    "Skipping periodic %s - API unavailable (%s)",
                    script,
                    profile.get("health_url"),
                )
                time.sleep(interval)
                continue

            script_path = self._resolve_script_path(script)
            cmd = [sys.executable, str(script_path)]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.base_dir,
                    timeout=max(interval - 1, 20),
                    env=self._child_env(),
                )
                if result.returncode != 0:
                    logger.warning(
                        f"Periodic script {script} exited with code {result.returncode}"
                    )
                    if result.stderr:
                        for line in result.stderr.splitlines()[-8:]:
                            if line.strip():
                                logger.warning(f"{script} STDERR: {line.strip()}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Periodic script {script} timed out")
            except Exception as e:
                logger.error(f"Periodic script error ({script}): {str(e)}")

            time.sleep(interval)

    def start_periodic_monitoring(self):
        """Start periodic one-shot checks that should not be supervised as daemons."""
        for profile in self.periodic_profiles:
            thread = threading.Thread(
                target=self._run_periodic_script,
                args=(profile,),
                daemon=True,
            )
            thread.start()
            self.monitoring_threads.append(thread)
            logger.info(
                "Scheduled periodic script %s every %ss",
                profile["script"],
                profile["interval"],
            )

    def _attempt_start_pending_profiles(self):
        if not self.pending_persistent_profiles:
            return

        remaining = []
        for profile in self.pending_persistent_profiles:
            script = profile["script"]
            if self._profile_can_start(profile):
                process_id = self.start_monitoring_process(
                    script,
                    continuous=True,
                    profile_name="persistent",
                )
                if process_id:
                    logger.info(
                        "Started deferred API-dependent monitor: %s",
                        script,
                    )
                else:
                    remaining.append(profile)
            else:
                remaining.append(profile)

        self.pending_persistent_profiles = remaining

    def start_continuous_audit(self):
        """Start continuous code quality monitoring"""
        logger.info("Starting continuous code quality monitoring")

        # Run Ruff check periodically
        def ruff_monitor():
            while self.running:
                try:
                    logger.info("Running Ruff code quality check...")
                    result = subprocess.run(
                        ["python", "-m", "ruff", "check", ".", "--statistics"],
                        capture_output=True,
                        text=True,
                        cwd=self.base_dir,
                        env=self._child_env(),
                    )
                    logger.info(
                        f"Ruff check completed. Return code: {result.returncode}"
                    )

                    # Log summary if available
                    if result.stdout:
                        lines = result.stdout.split("\n")
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
                active_processes = sum(
                    1 for p in self.processes.values() if p["status"] == "running"
                )
                total_processes = len(self.processes)

                logger.info(
                    f"System Health: {active_processes}/{total_processes} processes active"
                )

                # Check for failed processes
                failed_processes = [
                    p for p in self.processes.values() if p["status"] == "failed"
                ]
                if failed_processes:
                    logger.warning(f"{len(failed_processes)} processes in failed state")

                if self.pending_persistent_profiles:
                    logger.info(
                        f"Pending API-gated monitors: {len(self.pending_persistent_profiles)}"
                    )
                    self._attempt_start_pending_profiles()

                # Sleep for monitoring interval
                time.sleep(self.config["monitoring_interval"])

            except Exception as e:
                logger.error(f"System health monitoring error: {str(e)}")
                time.sleep(10)

    def stop_all_processes(self):
        """Stop all monitoring processes"""
        logger.info("Stopping all monitoring processes")

        for process_id, process_info in self.processes.items():
            try:
                process = process_info["process"]
                if process.poll() is None:  # Still running
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"Stopped {process_id}")
                stderr_handle = process_info.get("stderr_handle")
                if stderr_handle and not stderr_handle.closed:
                    stderr_handle.close()
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

            # Start periodic one-shot checks
            self.start_periodic_monitoring()

            # Start continuous audit
            self.start_continuous_audit()

            # Start system health monitoring
            health_thread = threading.Thread(
                target=self.monitor_system_health, daemon=True
            )
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
