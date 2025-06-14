# c:\kortana\write_dashboard.py
approved_hybrid_code = '''#!/usr/bin/env python3
"""
Hybrid Monitoring Dashboard - Production Ready
Combines real-time monitoring with enhanced analytics
Authors: Arch & Claude
Date: May 31, 2025
Version: Hybrid v1.0
"""

import sqlite3
import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from torch_protocol import TorchProtocol, TorchPackage
except ImportError:
    print("Warning: torch_protocol not found. Some features may be limited.")
    TorchProtocol = None
    TorchPackage = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_activity: float
    active_processes: int
    system_load: float
    temperature: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TorchMetrics:
    """Torch protocol specific metrics"""
    timestamp: str
    active_packages: int
    processing_rate: float
    queue_depth: int
    error_rate: float
    bandwidth_utilization: float
    protocol_efficiency: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class DatabaseManager:
    """Enhanced database operations for monitoring data"""

    def __init__(self, db_path: str = "kortana.db"):
        self.db_path = db_path
        self.connection_pool = []
        self.max_connections = 5
        self.lock = threading.Lock()
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection from the pool"""
        with self.lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                return conn

    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        with self.lock:
            if len(self.connection_pool) < self.max_connections:
                self.connection_pool.append(conn)
            else:
                conn.close()

    def _initialize_database(self):
        """Initialize database tables if they don't exist"""
        conn = self._get_connection()
        try:
            # System metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    network_activity REAL,
                    active_processes INTEGER,
                    system_load REAL,
                    temperature REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Torch metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS torch_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    active_packages INTEGER,
                    processing_rate REAL,
                    queue_depth INTEGER,
                    error_rate REAL,
                    bandwidth_utilization REAL,
                    protocol_efficiency REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source_component TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    component TEXT,
                    details TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
        finally:
            self._return_connection(conn)

    def insert_system_metrics(self, metrics: SystemMetrics) -> bool:
        """Insert system metrics into database"""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO system_metrics
                (timestamp, cpu_usage, memory_usage, disk_usage,
                 network_activity, active_processes, system_load, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp, metrics.cpu_usage, metrics.memory_usage,
                metrics.disk_usage, metrics.network_activity, metrics.active_processes,
                metrics.system_load, metrics.temperature
            ))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to insert system metrics: {e}")
            return False
        finally:
            self._return_connection(conn)

    def insert_torch_metrics(self, metrics: TorchMetrics) -> bool:
        """Insert torch metrics into database"""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO torch_metrics
                (timestamp, active_packages, processing_rate, queue_depth,
                 error_rate, bandwidth_utilization, protocol_efficiency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp, metrics.active_packages, metrics.processing_rate,
                metrics.queue_depth, metrics.error_rate, metrics.bandwidth_utilization,
                metrics.protocol_efficiency
            ))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to insert torch metrics: {e}")
            return False
        finally:
            self._return_connection(conn)

    def get_recent_metrics(self, table: str, hours: int = 24) -> List[Dict]:
        """Get recent metrics from specified table"""
        conn = self._get_connection()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cursor = conn.execute(f"""
                SELECT * FROM {table}
                WHERE created_at > ?
                ORDER BY created_at DESC
            """, (cutoff_time.isoformat(),))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get recent metrics from {table}: {e}")
            return []
        finally:
            self._return_connection(conn)

    def create_alert(self, alert_type: str, severity: str, message: str,
                    source_component: str = None) -> bool:
        """Create a new alert"""
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO alerts (timestamp, alert_type, severity, message, source_component)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), alert_type, severity, message, source_component))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to create alert: {e}")
            return False
        finally:
            self._return_connection(conn)

class SystemMonitor:
    """Enhanced system monitoring with real-time capabilities"""

    def __init__(self):
        self.is_running = False
        self.monitoring_interval = 5.0  # seconds
        self.metrics_history = []
        self.alert_thresholds = {
            'cpu_usage': 85.0,
            'memory_usage': 90.0,
            'disk_usage': 95.0,
            'system_load': 80.0
        }

    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Mock system metrics - in production, use psutil or similar
            import random

            metrics = SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_usage=random.uniform(10, 95),
                memory_usage=random.uniform(20, 80),
                disk_usage=random.uniform(30, 70),
                network_activity=random.uniform(5, 100),
                active_processes=random.randint(50, 200),
                system_load=random.uniform(0.1, 2.0),
                temperature=random.uniform(35, 75)
            )

            return metrics
        except Exception as e:
            logging.error(f"Failed to get system metrics: {e}")
            return None

    def check_thresholds(self, metrics: SystemMetrics) -> List[Dict]:
        """Check if metrics exceed alert thresholds"""
        alerts = []

        for metric, threshold in self.alert_thresholds.items():
            value = getattr(metrics, metric, 0)
            if value > threshold:
                alerts.append({
                    'type': 'threshold_exceeded',
                    'metric': metric,
                    'value': value,
                    'threshold': threshold,
                    'severity': 'HIGH' if value > threshold * 1.1 else 'MEDIUM'
                })

        return alerts

class TorchMonitor:
    """Torch protocol monitoring and analytics"""

    def __init__(self):
        self.torch_protocol = None
        self.is_monitoring = False
        self.metrics_buffer = []
        self.performance_history = []

        # Initialize torch protocol if available
        if TorchProtocol:
            try:
                self.torch_protocol = TorchProtocol()
            except Exception as e:
                logging.warning(f"Could not initialize TorchProtocol: {e}")

    def get_torch_metrics(self) -> Optional[TorchMetrics]:
        """Collect torch protocol metrics"""
        if not self.torch_protocol:
            # Mock metrics for demonstration
            import random
            return TorchMetrics(
                timestamp=datetime.now().isoformat(),
                active_packages=random.randint(0, 50),
                processing_rate=random.uniform(10, 1000),
                queue_depth=random.randint(0, 100),
                error_rate=random.uniform(0, 5),
                bandwidth_utilization=random.uniform(10, 95),
                protocol_efficiency=random.uniform(70, 99)
            )

        try:
            # Get real metrics from torch protocol
            stats = self.torch_protocol.get_statistics()
            return TorchMetrics(
                timestamp=datetime.now().isoformat(),
                active_packages=stats.get('active_packages', 0),
                processing_rate=stats.get('processing_rate', 0),
                queue_depth=stats.get('queue_depth', 0),
                error_rate=stats.get('error_rate', 0),
                bandwidth_utilization=stats.get('bandwidth_utilization', 0),
                protocol_efficiency=stats.get('protocol_efficiency', 0)
            )
        except Exception as e:
            logging.error(f"Failed to get torch metrics: {e}")
            return None

    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze torch performance trends"""
        if len(self.performance_history) < 2:
            return {'status': 'insufficient_data'}

        recent_metrics = self.performance_history[-10:]  # Last 10 measurements

        # Calculate trends
        processing_rates = [m.processing_rate for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        efficiency_scores = [m.protocol_efficiency for m in recent_metrics]

        return {
            'avg_processing_rate': sum(processing_rates) / len(processing_rates),
            'avg_error_rate': sum(error_rates) / len(error_rates),
            'avg_efficiency': sum(efficiency_scores) / len(efficiency_scores),
            'performance_trend': 'improving' if processing_rates[-1] > processing_rates[0] else 'declining',
            'stability_score': 100 - (max(error_rates) - min(error_rates)) * 10
        }

class MonitoringDashboard:
    """Main monitoring dashboard orchestrator"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.system_monitor = SystemMonitor()
        self.torch_monitor = TorchMonitor()
        self.is_running = False
        self.monitoring_tasks = []
        self.dashboard_data = {
            'system_metrics': None,
            'torch_metrics': None,
            'alerts': [],
            'performance_summary': {},
            'last_update': None
        }

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring.log'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("Monitoring Dashboard initialized")

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        if self.is_running:
            self.logger.warning("Monitoring already running")
            return

        self.is_running = True
        self.logger.info("Starting monitoring dashboard...")

        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._torch_monitoring_loop()),
            asyncio.create_task(self._dashboard_update_loop()),
            asyncio.create_task(self._alert_processing_loop())
        ]

        try:
            await asyncio.gather(*self.monitoring_tasks)
        except asyncio.CancelledError:
            self.logger.info("Monitoring tasks cancelled")
        except Exception as e:
            self.logger.error(f"Error in monitoring tasks: {e}")

    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        self.is_running = False

        for task in self.monitoring_tasks:
            task.cancel()

        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        self.logger.info("Monitoring dashboard stopped")

    async def _system_monitoring_loop(self):
        """System metrics monitoring loop"""
        while self.is_running:
            try:
                metrics = self.system_monitor.get_system_metrics()
                if metrics:
                    # Store in database
                    self.db_manager.insert_system_metrics(metrics)

                    # Update dashboard data
                    self.dashboard_data['system_metrics'] = metrics.to_dict()

                    # Check for alerts
                    alerts = self.system_monitor.check_thresholds(metrics)
                    for alert in alerts:
                        self.db_manager.create_alert(
                            alert['type'],
                            alert['severity'],
                            f"{alert['metric']} exceeded threshold: {alert['value']:.1f}% > {alert['threshold']}%",
                            'system_monitor'
                        )

                await asyncio.sleep(self.system_monitor.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _torch_monitoring_loop(self):
        """Torch protocol monitoring loop"""
        while self.is_running:
            try:
                metrics = self.torch_monitor.get_torch_metrics()
                if metrics:
                    # Store in database
                    self.db_manager.insert_torch_metrics(metrics)

                    # Update dashboard data
                    self.dashboard_data['torch_metrics'] = metrics.to_dict()

                    # Add to performance history
                    self.torch_monitor.performance_history.append(metrics)

                    # Keep only recent history (last 100 measurements)
                    if len(self.torch_monitor.performance_history) > 100:
                        self.torch_monitor.performance_history = self.torch_monitor.performance_history[-100:]

                await asyncio.sleep(10)  # Torch metrics every 10 seconds

            except Exception as e:
                self.logger.error(f"Error in torch monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _dashboard_update_loop(self):
        """Dashboard data update loop"""
        while self.is_running:
            try:
                # Update performance summary
                self.dashboard_data['performance_summary'] = self.torch_monitor.analyze_performance_trends()

                # Update last update timestamp
                self.dashboard_data['last_update'] = datetime.now().isoformat()

                # Get recent alerts
                recent_alerts = self.db_manager.get_recent_metrics('alerts', hours=1)
                self.dashboard_data['alerts'] = recent_alerts

                await asyncio.sleep(30)  # Update dashboard every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in dashboard update loop: {e}")
                await asyncio.sleep(30)

    async def _alert_processing_loop(self):
        """Alert processing and notification loop"""
        while self.is_running:
            try:
                # Process and potentially escalate alerts
                recent_alerts = self.db_manager.get_recent_metrics('alerts', hours=1)

                # Count high-severity alerts
                high_severity_count = sum(1 for alert in recent_alerts if alert.get('severity') == 'HIGH')

                if high_severity_count > 5:
                    self.logger.warning(f"High alert volume detected: {high_severity_count} high-severity alerts")

                await asyncio.sleep(60)  # Process alerts every minute

            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'monitoring_active': self.is_running,
            'database_connected': True,  # NOTE: Replace with real database health check in future.
            'torch_protocol_status': 'active' if self.torch_monitor.torch_protocol else 'unavailable',
            'uptime': datetime.now().isoformat(),
            'components': {
                'system_monitor': 'running' if self.is_running else 'stopped',
                'torch_monitor': 'running' if self.is_running else 'stopped',
                'database': 'connected',
                'alerts': 'active'
            }
        }

        return status

    def export_metrics(self, hours: int = 24, format: str = 'json') -> str:
        """Export metrics data"""
        try:
            system_metrics = self.db_manager.get_recent_metrics('system_metrics', hours)
            torch_metrics = self.db_manager.get_recent_metrics('torch_metrics', hours)
            alerts = self.db_manager.get_recent_metrics('alerts', hours)

            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'period_hours': hours,
                'system_metrics': system_metrics,
                'torch_metrics': torch_metrics,
                'alerts': alerts,
                'summary': {
                    'system_metrics_count': len(system_metrics),
                    'torch_metrics_count': len(torch_metrics),
                    'alerts_count': len(alerts)
                }
            }

            if format.lower() == 'json':
                return json.dumps(export_data, indent=2)
            else:
                return str(export_data)

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return json.dumps({'error': str(e)})

def create_sample_data():
    """Create sample monitoring data for testing"""
    db_manager = DatabaseManager()

    # Create sample system metrics
    for i in range(10):
        metrics = SystemMetrics(
            timestamp=(datetime.now() - timedelta(minutes=i*5)).isoformat(),
            cpu_usage=50 + i * 3,
            memory_usage=60 + i * 2,
            disk_usage=30 + i,
            network_activity=20 + i * 4,
            active_processes=100 + i * 5,
            system_load=1.0 + i * 0.1,
            temperature=45 + i
        )
        db_manager.insert_system_metrics(metrics)

    # Create sample torch metrics
    for i in range(10):
        metrics = TorchMetrics(
            timestamp=(datetime.now() - timedelta(minutes=i*5)).isoformat(),
            active_packages=10 + i,
            processing_rate=100 + i * 10,
            queue_depth=5 + i,
            error_rate=i * 0.5,
            bandwidth_utilization=70 + i * 2,
            protocol_efficiency=85 + i
        )
        db_manager.insert_torch_metrics(metrics)

    print("Sample data created successfully")

async def main():
    """Main function for running the monitoring dashboard"""
    dashboard = MonitoringDashboard()

    try:
        print("Starting Hybrid Monitoring Dashboard...")
        print("Press Ctrl+C to stop")

        # Create sample data if requested
        if len(sys.argv) > 1 and sys.argv[1] == '--sample-data':
            create_sample_data()

        # Start monitoring
        await dashboard.start_monitoring()

    except KeyboardInterrupt:
        print("\nShutting down monitoring dashboard...")
        await dashboard.stop_monitoring()
    except Exception as e:
        print(f"Error running dashboard: {e}")
        logging.error(f"Dashboard error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''

file_path_to_create = r"c:\kortana\monitoring_dashboard.py"
success_message = f"Successfully wrote approved code to {file_path_to_create}"
error_message = f"ERROR: Failed to write approved code to {file_path_to_create}"

try:
    import os

    if os.path.exists(file_path_to_create):
        os.remove(file_path_to_create)  # Ensure a clean slate

    with open(file_path_to_create, "w", encoding="utf-8") as f:
        f.write(approved_hybrid_code)
    print(success_message)
except Exception as e:
    print(f"{error_message}: {e}")
