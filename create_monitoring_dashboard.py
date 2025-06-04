#!/usr/bin/env python3

import json
import logging
import signal
import sqlite3
import sys
import threading
import time
import traceback
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("monitoring_dashboard.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    torch_packages_processed: int
    error_count: int
    warning_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "network_io": self.network_io,
            "active_connections": self.active_connections,
            "torch_packages_processed": self.torch_packages_processed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }


@dataclass
class TorchMetrics:
    package_id: str
    processing_time: float
    status: str
    relay_node: str
    throughput: float
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlertConfig:
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True


@dataclass
class Alert:
    id: str
    config: AlertConfig
    triggered_at: datetime
    value: float
    message: str
    acknowledged: bool = False
    resolved: bool = False


class DatabaseManager:
    def __init__(self, db_path: str = "kortana.db"):
        self.db_path = db_path
        self.connection = None
        self._lock = threading.Lock()
        self.init_monitoring_tables()

    def connect(self) -> sqlite3.Connection:
        """Create a new database connection for the current thread."""
        return sqlite3.connect(self.db_path, timeout=30.0)

    def init_monitoring_tables(self):
        """Initialize monitoring tables if they don't exist."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()

                # System metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        network_io TEXT,
                        active_connections INTEGER,
                        torch_packages_processed INTEGER,
                        error_count INTEGER,
                        warning_count INTEGER
                    )
                """)

                # Torch metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS torch_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        package_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        processing_time REAL,
                        status TEXT,
                        relay_node TEXT,
                        throughput REAL,
                        error_details TEXT
                    )
                """)

                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        metric_name TEXT NOT NULL,
                        threshold REAL,
                        comparison TEXT,
                        severity TEXT,
                        triggered_at TEXT,
                        value REAL,
                        message TEXT,
                        acknowledged BOOLEAN DEFAULT 0,
                        resolved BOOLEAN DEFAULT 0
                    )
                """)

                # Alert configurations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_configs (
                        metric_name TEXT PRIMARY KEY,
                        threshold REAL,
                        comparison TEXT,
                        severity TEXT,
                        enabled BOOLEAN DEFAULT 1
                    )
                """)

                conn.commit()
                logger.info("Monitoring tables initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring tables: {e}")
            raise

    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO system_metrics
                    (timestamp, cpu_usage, memory_usage, disk_usage, network_io,
                     active_connections, torch_packages_processed, error_count, warning_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.timestamp.isoformat(),
                        metrics.cpu_usage,
                        metrics.memory_usage,
                        metrics.disk_usage,
                        json.dumps(metrics.network_io),
                        metrics.active_connections,
                        metrics.torch_packages_processed,
                        metrics.error_count,
                        metrics.warning_count,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store system metrics: {e}")

    def store_torch_metrics(self, metrics: TorchMetrics):
        """Store torch metrics in database."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO torch_metrics
                    (package_id, timestamp, processing_time, status, relay_node, throughput, error_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metrics.package_id,
                        datetime.now().isoformat(),
                        metrics.processing_time,
                        metrics.status,
                        metrics.relay_node,
                        metrics.throughput,
                        metrics.error_details,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store torch metrics: {e}")

    def store_alert(self, alert: Alert):
        """Store alert in database."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO alerts
                    (id, metric_name, threshold, comparison, severity, triggered_at, value, message, acknowledged, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        alert.id,
                        alert.config.metric_name,
                        alert.config.threshold,
                        alert.config.comparison,
                        alert.config.severity,
                        alert.triggered_at.isoformat(),
                        alert.value,
                        alert.message,
                        alert.acknowledged,
                        alert.resolved,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")

    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent system metrics."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                since = (datetime.now() - timedelta(hours=hours)).isoformat()
                cursor.execute(
                    """
                    SELECT * FROM system_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (since,),
                )

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []

    def get_torch_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent torch metrics."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                since = (datetime.now() - timedelta(hours=hours)).isoformat()
                cursor.execute(
                    """
                    SELECT * FROM torch_metrics
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """,
                    (since,),
                )

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get torch metrics: {e}")
            return []

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM alerts
                    WHERE resolved = 0
                    ORDER BY triggered_at DESC
                """)

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []


class MetricsCollector:
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.torch_metrics_history = deque(maxlen=1000)

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            import psutil

            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            # Get disk usage
            disk = psutil.disk_usage("/")
            disk_usage = (disk.used / disk.total) * 100

            # Get network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            # Get connection count
            connections = len(psutil.net_connections())

            # Placeholder values for torch-specific metrics
            torch_packages = self._get_torch_packages_count()
            error_count = self._get_error_count()
            warning_count = self._get_warning_count()

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                torch_packages_processed=torch_packages,
                error_count=error_count,
                warning_count=warning_count,
            )

            self.metrics_history.append(metrics)
            return metrics

        except ImportError:
            logger.warning("psutil not available, using mock metrics")
            return self._get_mock_metrics()
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return self._get_mock_metrics()

    def _get_mock_metrics(self) -> SystemMetrics:
        """Generate mock metrics for testing."""
        import random

        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=random.uniform(10, 80),
            memory_usage=random.uniform(20, 70),
            disk_usage=random.uniform(15, 60),
            network_io={
                "bytes_sent": random.randint(1000, 10000),
                "bytes_recv": random.randint(1000, 10000),
            },
            active_connections=random.randint(5, 50),
            torch_packages_processed=random.randint(0, 100),
            error_count=random.randint(0, 5),
            warning_count=random.randint(0, 10),
        )

    def _get_torch_packages_count(self) -> int:
        """Get count of torch packages processed."""
        try:
            # This would integrate with the actual torch system
            return len(self.torch_metrics_history)
        except Exception:
            return 0

    def _get_error_count(self) -> int:
        """Get current error count."""
        # This would integrate with logging system
        return 0

    def _get_warning_count(self) -> int:
        """Get current warning count."""
        # This would integrate with logging system
        return 0


class AlertManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.alert_configs = self._load_alert_configs()
        self.active_alerts = {}

    def _load_alert_configs(self) -> Dict[str, AlertConfig]:
        """Load alert configurations from database."""
        configs = {}
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM alert_configs WHERE enabled = 1")

                for row in cursor.fetchall():
                    config = AlertConfig(
                        metric_name=row[0],
                        threshold=row[1],
                        comparison=row[2],
                        severity=row[3],
                        enabled=bool(row[4]),
                    )
                    configs[config.metric_name] = config
        except Exception as e:
            logger.error(f"Failed to load alert configs: {e}")

        # Default configurations if none exist
        if not configs:
            configs = self._get_default_alert_configs()
            self._save_default_configs(configs)

        return configs

    def _get_default_alert_configs(self) -> Dict[str, AlertConfig]:
        """Get default alert configurations."""
        return {
            "cpu_usage": AlertConfig("cpu_usage", 80.0, "gt", "high"),
            "memory_usage": AlertConfig("memory_usage", 85.0, "gt", "high"),
            "disk_usage": AlertConfig("disk_usage", 90.0, "gt", "critical"),
            "error_count": AlertConfig("error_count", 5.0, "gt", "medium"),
            "torch_packages_processed": AlertConfig(
                "torch_packages_processed", 1000.0, "gt", "low"
            ),
        }

    def _save_default_configs(self, configs: Dict[str, AlertConfig]):
        """Save default configurations to database."""
        try:
            with self.db_manager.connect() as conn:
                cursor = conn.cursor()
                for config in configs.values():
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO alert_configs
                        (metric_name, threshold, comparison, severity, enabled)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            config.metric_name,
                            config.threshold,
                            config.comparison,
                            config.severity,
                            config.enabled,
                        ),
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save default alert configs: {e}")

    def check_alerts(self, metrics: SystemMetrics):
        """Check metrics against alert configurations."""
        metrics_dict = metrics.to_dict()

        for metric_name, config in self.alert_configs.items():
            if not config.enabled:
                continue

            if metric_name in metrics_dict:
                value = metrics_dict[metric_name]
                if isinstance(value, (int, float)):
                    should_alert = self._evaluate_threshold(value, config)

                    if should_alert:
                        alert_id = f"{metric_name}_{int(time.time())}"
                        alert = Alert(
                            id=alert_id,
                            config=config,
                            triggered_at=datetime.now(),
                            value=value,
                            message=f"{metric_name} is {value} (threshold: {config.threshold})",
                        )

                        self.active_alerts[alert_id] = alert
                        self.db_manager.store_alert(alert)
                        logger.warning(f"Alert triggered: {alert.message}")

    def _evaluate_threshold(self, value: float, config: AlertConfig) -> bool:
        """Evaluate if value exceeds threshold based on comparison type."""
        if config.comparison == "gt":
            return value > config.threshold
        elif config.comparison == "lt":
            return value < config.threshold
        elif config.comparison == "eq":
            return abs(value - config.threshold) < 0.01
        return False


class MonitoringDashboard:
    def __init__(self, db_path: str = "kortana.db"):
        self.db_manager = DatabaseManager(db_path)
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.db_manager)
        self.running = False
        self.monitor_thread = None
        self._stop_event = threading.Event()

        # Web server components (if needed)
        self.web_server = None

        logger.info("Monitoring Dashboard initialized")

    def start_monitoring(self, interval: int = 60):
        """Start the monitoring loop."""
        if self.running:
            logger.warning("Monitoring is already running")
            return

        self.running = True
        self._stop_event.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Monitoring started with {interval}s interval")

    def stop_monitoring(self):
        """Stop the monitoring loop."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

        logger.info("Monitoring stopped")

    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        logger.info("Monitoring loop started")

        while self.running and not self._stop_event.is_set():
            try:
                # Collect metrics
                metrics = self.metrics_collector.collect_system_metrics()

                # Store metrics
                self.db_manager.store_system_metrics(metrics)

                # Check for alerts
                self.alert_manager.check_alerts(metrics)

                # Log current status
                logger.info(
                    f"Metrics collected - CPU: {metrics.cpu_usage:.1f}%, "
                    f"Memory: {metrics.memory_usage:.1f}%, "
                    f"Disk: {metrics.disk_usage:.1f}%"
                )

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.error(traceback.format_exc())

            # Wait for next interval
            if not self._stop_event.wait(interval):
                continue

        logger.info("Monitoring loop ended")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        try:
            # Get recent metrics
            recent_metrics = self.db_manager.get_recent_metrics(hours=24)
            torch_metrics = self.db_manager.get_torch_metrics(hours=24)
            active_alerts = self.db_manager.get_active_alerts()

            # Calculate aggregated statistics
            stats = self._calculate_stats(recent_metrics)

            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy" if len(active_alerts) == 0 else "warning",
                "recent_metrics": recent_metrics[-10:] if recent_metrics else [],
                "torch_metrics": torch_metrics[-10:] if torch_metrics else [],
                "active_alerts": active_alerts,
                "stats": stats,
                "monitoring_status": "running" if self.running else "stopped",
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "error",
                "error": str(e),
            }

    def _calculate_stats(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregated statistics from metrics data."""
        if not metrics_data:
            return {}

        try:
            cpu_values = [
                m["cpu_usage"] for m in metrics_data if m.get("cpu_usage") is not None
            ]
            memory_values = [
                m["memory_usage"]
                for m in metrics_data
                if m.get("memory_usage") is not None
            ]

            stats = {}

            if cpu_values:
                stats["cpu"] = {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values),
                    "current": cpu_values[-1] if cpu_values else 0,
                }

            if memory_values:
                stats["memory"] = {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values),
                    "current": memory_values[-1] if memory_values else 0,
                }

            return stats
        except Exception as e:
            logger.error(f"Failed to calculate stats: {e}")
            return {}

    def generate_report(self, hours: int = 24) -> str:
        """Generate a text report of system status."""
        try:
            data = self.get_dashboard_data()
            stats = data.get("stats", {})
            alerts = data.get("active_alerts", [])

            report = []
            report.append("=== KORTANA MONITORING REPORT ===")
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(
                f"System Status: {data.get('system_status', 'unknown').upper()}"
            )
            report.append("")

            # System metrics summary
            if stats.get("cpu"):
                cpu = stats["cpu"]
                report.append(
                    f"CPU Usage - Current: {cpu['current']:.1f}%, Avg: {cpu['avg']:.1f}%, Max: {cpu['max']:.1f}%"
                )

            if stats.get("memory"):
                memory = stats["memory"]
                report.append(
                    f"Memory Usage - Current: {memory['current']:.1f}%, Avg: {memory['avg']:.1f}%, Max: {memory['max']:.1f}%"
                )

            report.append("")

            # Active alerts
            if alerts:
                report.append("ACTIVE ALERTS:")
                for alert in alerts:
                    report.append(f"- [{alert['severity'].upper()}] {alert['message']}")
            else:
                report.append("No active alerts")

            report.append("")
            report.append("=== END REPORT ===")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return f"Error generating report: {e}"


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    sys.exit(0)


def main():
    """Main entry point for the monitoring dashboard."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize dashboard
        dashboard = MonitoringDashboard()

        # Start monitoring
        dashboard.start_monitoring(interval=60)  # 60 second intervals

        logger.info("Monitoring dashboard started successfully")
        logger.info("Press Ctrl+C to stop")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)

                # Optional: Print periodic status
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    data = dashboard.get_dashboard_data()
                    logger.info(f"Status: {data.get('system_status', 'unknown')}")

        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")

    except Exception as e:
        logger.error(f"Failed to start monitoring dashboard: {e}")
        logger.error(traceback.format_exc())
        return 1

    finally:
        # Clean shutdown
        if "dashboard" in locals():
            dashboard.stop_monitoring()
        logger.info("Monitoring dashboard stopped")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
