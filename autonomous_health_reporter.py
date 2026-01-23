"""
Autonomous Health Reporter - Status & Intelligence Reporting System
====================================================================

This service generates:
- System health reports
- Autonomous intelligence status reports
- Development progress summaries
- Performance metrics and dashboards
- Alert notifications for critical issues

Reports are saved to JSON, markdown, and sent to monitoring systems.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state/health_reports.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Path('state').mkdir(exist_ok=True)
Path('state/reports').mkdir(exist_ok=True)


class AutonomousHealthReporter:
    """Generates comprehensive health and status reports."""
    
    def __init__(self):
        self.monitor_db = 'state/autonomous_activity.db'
        self.task_db = 'state/autonomous_tasks.db'
        self.dev_db = 'state/development_activity.db'
        self.reports_dir = 'state/reports'
        self.is_running = False
        self.report_interval = 300  # 5 minutes between reports
        self.last_critical_alert = None
        
        logger.info("🟢 Autonomous Health Reporter initialized")
    
    def _read_json_file(self, file_path: str) -> Optional[Dict]:
        """Safely read a JSON file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
        return None
    
    def _get_monitor_data(self) -> Dict[str, Any]:
        """Get data from monitor database."""
        data = {
            'latest_metrics': None,
            'recent_activities': [],
            'uptime_hours': 0
        }
        
        try:
            if os.path.exists(self.monitor_db):
                conn = sqlite3.connect(self.monitor_db)
                cursor = conn.cursor()
                
                # Latest health metrics
                cursor.execute('''
                    SELECT cpu_percent, memory_percent, memory_mb, disk_percent,
                           api_status, db_status, uptime_minutes
                    FROM health_metrics
                    ORDER BY timestamp DESC LIMIT 1
                ''')
                row = cursor.fetchone()
                if row:
                    data['latest_metrics'] = {
                        'cpu': row[0],
                        'memory': row[1],
                        'memory_mb': row[2],
                        'disk': row[3],
                        'api_status': row[4],
                        'db_status': row[5],
                        'uptime_hours': row[6] / 60
                    }
                
                # Recent activities
                cursor.execute('''
                    SELECT activity_type, description, status, timestamp
                    FROM activities
                    ORDER BY timestamp DESC LIMIT 10
                ''')
                data['recent_activities'] = [
                    {
                        'type': row[0],
                        'description': row[1],
                        'status': row[2],
                        'time': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to get monitor data: {e}")
        
        return data
    
    def _get_task_data(self) -> Dict[str, Any]:
        """Get data from task database."""
        data = {
            'total_tasks': 0,
            'completed': 0,
            'failed': 0,
            'pending': 0,
            'recent_executions': []
        }
        
        try:
            if os.path.exists(self.task_db):
                conn = sqlite3.connect(self.task_db)
                cursor = conn.cursor()
                
                # Task counts
                cursor.execute('''
                    SELECT status, COUNT(*) FROM tasks GROUP BY status
                ''')
                for row in cursor.fetchall():
                    if row[0] == 'completed':
                        data['completed'] = row[1]
                    elif row[0] == 'failed':
                        data['failed'] = row[1]
                    elif row[0] == 'pending':
                        data['pending'] = row[1]
                data['total_tasks'] = data['completed'] + data['failed'] + data['pending']
                
                # Recent task executions
                cursor.execute('''
                    SELECT task_id, status, duration_ms, timestamp
                    FROM task_executions
                    ORDER BY timestamp DESC LIMIT 10
                ''')
                data['recent_executions'] = [
                    {
                        'task_id': row[0],
                        'status': row[1],
                        'duration_ms': row[2],
                        'time': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to get task data: {e}")
        
        return data
    
    def _get_development_data(self) -> Dict[str, Any]:
        """Get data from development activity database."""
        data = {
            'files_changed_24h': 0,
            'tests_run': 0,
            'code_quality': None,
            'milestones': []
        }
        
        try:
            if os.path.exists(self.dev_db):
                conn = sqlite3.connect(self.dev_db)
                cursor = conn.cursor()
                
                # File changes in last 24 hours
                cursor.execute('''
                    SELECT COUNT(*) FROM file_changes
                    WHERE timestamp > datetime('now', '-24 hours')
                ''')
                data['files_changed_24h'] = cursor.fetchone()[0]
                
                # Test executions
                cursor.execute('''
                    SELECT COUNT(*) FROM test_executions
                    WHERE timestamp > datetime('now', '-24 hours')
                ''')
                data['tests_run'] = cursor.fetchone()[0]
                
                # Latest code quality
                cursor.execute('''
                    SELECT total_files, lines_of_code, test_coverage, linter_issues
                    FROM code_quality_metrics
                    ORDER BY timestamp DESC LIMIT 1
                ''')
                row = cursor.fetchone()
                if row:
                    data['code_quality'] = {
                        'files': row[0],
                        'loc': row[1],
                        'coverage': row[2],
                        'linter_issues': row[3]
                    }
                
                # Recent milestones
                cursor.execute('''
                    SELECT milestone_type, description, impact_score, timestamp
                    FROM development_milestones
                    WHERE timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp DESC LIMIT 10
                ''')
                data['milestones'] = [
                    {
                        'type': row[0],
                        'description': row[1],
                        'impact': row[2],
                        'time': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                conn.close()
        except Exception as e:
            logger.warning(f"Failed to get development data: {e}")
        
        return data
    
    def _check_alerts(self, monitor_data: Dict) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        alerts = []
        
        if monitor_data.get('latest_metrics'):
            metrics = monitor_data['latest_metrics']
            
            # CPU alert
            if metrics.get('cpu', 0) > 80:
                alerts.append({
                    'severity': 'warning' if metrics['cpu'] < 95 else 'critical',
                    'type': 'HIGH_CPU',
                    'message': f"CPU usage at {metrics['cpu']:.1f}%"
                })
            
            # Memory alert
            if metrics.get('memory', 0) > 85:
                alerts.append({
                    'severity': 'warning' if metrics['memory'] < 95 else 'critical',
                    'type': 'HIGH_MEMORY',
                    'message': f"Memory usage at {metrics['memory']:.1f}%"
                })
            
            # Disk alert
            if metrics.get('disk', 0) > 90:
                alerts.append({
                    'severity': 'critical',
                    'type': 'HIGH_DISK',
                    'message': f"Disk usage at {metrics['disk']:.1f}%"
                })
            
            # Service alerts
            if metrics.get('api_status') != 'healthy':
                alerts.append({
                    'severity': 'critical',
                    'type': 'API_DOWN',
                    'message': f"API status: {metrics['api_status']}"
                })
            
            if metrics.get('db_status') != 'healthy':
                alerts.append({
                    'severity': 'critical',
                    'type': 'DATABASE_DOWN',
                    'message': f"Database status: {metrics['db_status']}"
                })
        
        return alerts
    
    def _generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        logger.info("📋 Generating health report...")
        
        monitor_data = self._get_monitor_data()
        task_data = self._get_task_data()
        dev_data = self._get_development_data()
        alerts = self._check_alerts(monitor_data)
        
        # Determine overall health status
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        overall_status = 'critical' if critical_alerts else 'healthy' if not alerts else 'warning'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'system_health': {
                'metrics': monitor_data.get('latest_metrics'),
                'uptime_hours': monitor_data.get('latest_metrics', {}).get('uptime_hours', 0),
                'recent_activities': len(monitor_data.get('recent_activities', []))
            },
            'task_execution': {
                'total_registered': task_data['total_tasks'],
                'completed': task_data['completed'],
                'pending': task_data['pending'],
                'failed': task_data['failed'],
                'recent_executions': len(task_data['recent_executions'])
            },
            'development_activity': {
                'files_changed_24h': dev_data['files_changed_24h'],
                'tests_run_24h': dev_data['tests_run'],
                'code_quality': dev_data['code_quality'],
                'milestones_7d': len(dev_data['milestones'])
            },
            'alerts': alerts,
            'critical_count': len(critical_alerts),
            'warning_count': len([a for a in alerts if a['severity'] == 'warning'])
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], report_type: str = 'health'):
        """Save report to JSON and markdown formats."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save JSON
            json_path = os.path.join(self.reports_dir, f'{report_type}_{timestamp}.json')
            with open(json_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Save markdown
            md_path = os.path.join(self.reports_dir, f'{report_type}_{timestamp}.md')
            with open(md_path, 'w') as f:
                f.write(self._report_to_markdown(report))
            
            logger.info(f"✅ Report saved: {json_path}")
            
        except Exception as e:
            logger.error(f"✗ Failed to save report: {e}")
    
    def _report_to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to markdown format."""
        md = f"""# Autonomous System Health Report

**Generated:** {report['timestamp']}
**Overall Status:** {report['overall_status'].upper()}

## 🔧 System Health

- **CPU Usage:** {report['system_health']['metrics'].get('cpu', 'N/A')}%
- **Memory Usage:** {report['system_health']['metrics'].get('memory', 'N/A')}%
- **Disk Usage:** {report['system_health']['metrics'].get('disk', 'N/A')}%
- **Uptime:** {report['system_health']['uptime_hours']:.1f} hours
- **API Status:** {report['system_health']['metrics'].get('api_status', 'unknown')}
- **Database Status:** {report['system_health']['metrics'].get('db_status', 'unknown')}

## 📋 Task Execution

- **Total Tasks:** {report['task_execution']['total_registered']}
- **Completed:** {report['task_execution']['completed']}
- **Pending:** {report['task_execution']['pending']}
- **Failed:** {report['task_execution']['failed']}
- **Recent Executions:** {report['task_execution']['recent_executions']}

## 🔨 Development Activity

- **Files Changed (24h):** {report['development_activity']['files_changed_24h']}
- **Tests Run (24h):** {report['development_activity']['tests_run_24h']}
- **Milestones (7d):** {report['development_activity']['milestones_7d']}

"""
        
        if report.get('code_quality'):
            qm = report['code_quality']
            md += f"""## 📊 Code Quality

- **Total Files:** {qm.get('files', 'N/A')}
- **Lines of Code:** {qm.get('loc', 'N/A')}
- **Test Coverage:** {qm.get('coverage', 'N/A')}%
- **Linter Issues:** {qm.get('linter_issues', 'N/A')}

"""
        
        if report['alerts']:
            md += f"## ⚠️  Alerts ({report['critical_count']} Critical, {report['warning_count']} Warnings)\n\n"
            for alert in report['alerts']:
                severity_emoji = '🔴' if alert['severity'] == 'critical' else '🟡'
                md += f"- {severity_emoji} **{alert['type']}**: {alert['message']}\n"
        else:
            md += "## ✅ No Alerts\n\n"
        
        return md
    
    def report_cycle(self):
        """Execute a single reporting cycle."""
        try:
            report = self._generate_health_report()
            
            # Log report
            logger.info(f"📊 Health Status: {report['overall_status'].upper()}")
            logger.info(f"   Tasks: {report['task_execution']['completed']} completed, "
                       f"{report['task_execution']['failed']} failed")
            logger.info(f"   Development: {report['development_activity']['files_changed_24h']} "
                       f"files changed, {report['development_activity']['tests_run_24h']} tests")
            
            if report['alerts']:
                logger.warning(f"   🚨 {len(report['alerts'])} alerts active")
                for alert in report['alerts']:
                    logger.warning(f"      {alert['severity'].upper()}: {alert['message']}")
            
            # Save report
            self.save_report(report, 'health')
            
            # Check for critical alerts
            critical_alerts = [a for a in report['alerts'] if a['severity'] == 'critical']
            if critical_alerts:
                self._handle_critical_alert(critical_alerts)
        
        except Exception as e:
            logger.error(f"✗ Report cycle failed: {e}")
    
    def _handle_critical_alert(self, alerts: List[Dict]):
        """Handle critical alerts."""
        logger.critical(f"🚨 CRITICAL ALERT: {len(alerts)} critical issues detected!")
        for alert in alerts:
            logger.critical(f"   - {alert['type']}: {alert['message']}")
    
    def run(self):
        """Start the health reporter."""
        self.is_running = True
        logger.info("🚀 Starting Autonomous Health Reporter")
        logger.info(f"⏱️  Report interval: {self.report_interval} seconds")
        
        try:
            while self.is_running:
                self.report_cycle()
                time.sleep(self.report_interval)
        except KeyboardInterrupt:
            logger.info("⏹️  Reporter interrupted by user")
        except Exception as e:
            logger.error(f"✗ Reporter error: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the reporter gracefully."""
        self.is_running = False
        logger.info("🛑 Autonomous Health Reporter shutdown")


def main():
    """Main entry point."""
    reporter = AutonomousHealthReporter()
    reporter.run()


if __name__ == '__main__':
    main()
