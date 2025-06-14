#!/usr/bin/env python3
"""
Enhanced Kor'tana System Monitoring Dashboard
=============================================
Real-time monitoring with token tracking, rate limits, and agent status.
"""

import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import tiktoken

# Configure logging
logger = logging.getLogger(__name__)


class KortanaEnhancedMonitor:
    """Enhanced monitoring dashboard for Kor'tana system with detailed analytics"""

    def __init__(self, project_root: str | None = None):
        """Initialize the monitor with project paths and database setup."""
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.db_path = self.project_root / "kortana.db"
        self.logs_dir = self.project_root / "logs"
        self.data_dir = self.project_root / "data"

        # Ensure required directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)        # Initialize monitoring tables
        self.init_monitor_tables()
        
    def count_tokens(self, text: str, encoding_name: str = "cl100k_base") -> int:
        """Count tokens in text using tiktoken with fallback."""
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except (KeyError, ImportError, ValueError) as e:
            # Log specific error for troubleshooting
            logger.warning(f"Token counting error: {str(e)}. Using fallback estimation.")
            # Fallback to simple word count estimation with integer rounding
            return int(len(text.split()) * 1.3)

    def init_monitor_tables(self) -> None:
        """Initialize monitoring tables in database."""
        if not self.db_path.exists():
            print(f"Database not found at: {self.db_path}")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Token usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    stage TEXT,
                    tokens INTEGER,
                    timestamp TEXT,
                    agent_name TEXT
                )
            """)

            # Chain of communication log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chain_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    stage TEXT,
                    tokens INTEGER,
                    timestamp TEXT,
                    agent_from TEXT,
                    agent_to TEXT
                )
            """)

            # Rate limit tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT,
                    requests_used INTEGER,
                    tokens_used INTEGER,
                    reset_time TEXT,
                    timestamp TEXT
                )
            """)

            conn.commit()
            conn.close()
        except (sqlite3.Error, sqlite3.OperationalError) as e:
            logger.error(f"Failed to initialize monitoring tables: {str(e)}")
            raise RuntimeError(f"Database initialization failed: {str(e)}") from e

    def log_token_usage(
        self, task_id: str, stage: str, tokens: int, agent_name: str = "system"
    ):
        """Log token usage to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_log (task_id, stage, tokens, timestamp, agent_name) VALUES (?, ?, ?, ?, ?)",
                (task_id, stage, tokens, datetime.utcnow().isoformat(), agent_name),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to log token usage: {str(e)}")
            # Don't raise here as token logging failure shouldn't stop the application

    def log_chain_communication(
        self, task_id: str, stage: str, tokens: int, agent_from: str, agent_to: str
    ):
        """Log agent-to-agent communication"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chain_log (task_id, stage, tokens, timestamp, agent_from, agent_to) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    stage,
                    tokens,
                    datetime.utcnow().isoformat(),
                    agent_from,
                    agent_to,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WARNING] Could not log chain communication: {e}")

    def get_active_agents(self) -> list[str]:
        """Get list of currently active agents"""
        agents = []

        # Check log files for recent activity
        if self.logs_dir.exists():
            for log_file in self.logs_dir.glob("*.log"):
                try:
                    # Check if file was modified in last hour
                    modified_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if (datetime.now() - modified_time) < timedelta(hours=1):
                        agents.append(log_file.stem)
                except OSError as e:
                    logger.warning(f"Error checking log file {log_file}: {str(e)}")

        # Also check database for recent activity
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            cursor.execute(
                "SELECT DISTINCT agent_name FROM token_log WHERE timestamp > ?",
                (one_hour_ago,),
            )
            db_agents = [row[0] for row in cursor.fetchall()]
            agents.extend(db_agents)
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database error while getting active agents: {str(e)}")
            
        return list(set(agents))

    def get_token_usage_stats(self) -> dict[str, Any]:
        """Get comprehensive token usage statistics"""
        stats = {
            "last_24h": {},
            "last_hour": {},
            "by_agent": {},
            "by_stage": {},
            "total_today": 0,
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Last 24 hours usage by stage
            one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
            cursor.execute(
                "SELECT stage, SUM(tokens) FROM token_log WHERE timestamp > ? GROUP BY stage",
                (one_day_ago,),
            )
            stats["last_24h"] = dict(cursor.fetchall())

            # Last hour usage
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            cursor.execute(
                "SELECT stage, SUM(tokens) FROM token_log WHERE timestamp > ? GROUP BY stage",
                (one_hour_ago,),
            )
            stats["last_hour"] = dict(cursor.fetchall())

            # Usage by agent
            cursor.execute(
                "SELECT agent_name, SUM(tokens) FROM token_log WHERE timestamp > ? GROUP BY agent_name",
                (one_day_ago,),
            )
            stats["by_agent"] = dict(cursor.fetchall())

            # Usage by stage (all time)
            cursor.execute("SELECT stage, SUM(tokens) FROM token_log GROUP BY stage")
            stats["by_stage"] = dict(cursor.fetchall())

            # Total today
            today_start = (
                datetime.utcnow()
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .isoformat()
            )
            cursor.execute(
                "SELECT SUM(tokens) FROM token_log WHERE timestamp > ?", (today_start,)
            )
            result = cursor.fetchone()
            stats["total_today"] = result[0] if result[0] else 0

            conn.close()
        except sqlite3.Error as e:
            stats.update({
                "error": "Database error",
                "details": str(e),
                "total_today": 0
            })
            logger.error(f"Failed to retrieve token usage stats: {str(e)}")

        return stats

    def get_rate_limit_status(self) -> dict[str, Any]:
        """Get rate limit status for various services"""
        # Rate limits based on current API tiers
        limits = {
            "gemini_flash": {
                "name": "Gemini 2.0 Flash",
                "tpm_limit": 1000000,  # 1M tokens per minute
                "rpm_limit": 1500,  # 1500 requests per minute
                "used_tokens": 0,
                "used_requests": 0,
            },
            "github_models": {
                "name": "GitHub Models",
                "requests_limit": 5000,  # Estimated daily limit
                "used_requests": 0,
            },
            "openrouter": {
                "name": "OpenRouter",
                "credits_limit": 100,  # Depends on plan
                "used_credits": 0,
            },
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate Gemini usage (last hour for TPM)
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            cursor.execute(
                "SELECT SUM(tokens) FROM token_log WHERE timestamp > ? AND stage IN ('summarize', 'init', 'process')",
                (one_hour_ago,),
            )
            result = cursor.fetchone()
            limits["gemini_flash"]["used_tokens"] = result[0] if result[0] else 0

            # Calculate request counts
            cursor.execute(
                "SELECT COUNT(*) FROM token_log WHERE timestamp > ?", (one_hour_ago,)
            )
            result = cursor.fetchone()
            limits["gemini_flash"]["used_requests"] = result[0] if result[0] else 0

            # Calculate GitHub Models usage (daily)
            today_start = (
                datetime.utcnow()
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .isoformat()
            )
            cursor.execute(
                "SELECT COUNT(*) FROM chain_log WHERE timestamp > ? AND stage = 'test'",
                (today_start,),
            )
            result = cursor.fetchone()
            limits["github_models"]["used_requests"] = result[0] if result[0] else 0

            conn.close()
        except (sqlite3.Error, sqlite3.OperationalError) as e:
            # Initialize an error state model matching the expected structure
            limits = {
                "openai_models": {"used_tokens": 0, "tpm_limit": 1000, "rpm_limit": 100},
                "github_models": {"used_requests": 0, "requests_limit": 100},
                "error_details": {"message": str(e), "timestamp": datetime.utcnow().isoformat()}
            }
            logger.error(f"Failed to retrieve rate limits: {str(e)}")

        # Calculate percentages
        for service, data in limits.items():
            if service == "error_details":
                continue
            if "tpm_limit" in data:
                data["tpm_percent"] = (
                    (data["used_tokens"] / data["tpm_limit"]) * 100
                    if data["tpm_limit"] > 0
                    else 0
                )
            if "rpm_limit" in data:
                data["rpm_percent"] = (
                    (data["used_requests"] / data["rpm_limit"]) * 100
                    if data["rpm_limit"] > 0
                    else 0
                )
            if "requests_limit" in data:
                data["requests_percent"] = (
                    (data["used_requests"] / data["requests_limit"]) * 100
                    if data["requests_limit"] > 0
                    else 0
                )

        return limits

    def get_context_window_status(self) -> dict[str, Any]:
        """Get context window utilization"""
        context_limits = {"gemini_flash": 128000, "claude": 200000, "gpt4": 128000}

        status = {}
        token_stats = self.get_token_usage_stats()

        for model, limit in context_limits.items():
            used = sum(token_stats["last_hour"].values())
            available = limit - used
            percent_used = (used / limit) * 100 if limit > 0 else 0

            status[model] = {
                "limit": limit,
                "used": used,
                "available": available,
                "percent_used": percent_used,
                "status": "optimal"
                if percent_used < 70
                else "warning"
                if percent_used < 90
                else "critical",
            }

        return status

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_agents": self.get_active_agents(),
            "token_usage": self.get_token_usage_stats(),
            "rate_limits": self.get_rate_limit_status(),
            "context_windows": self.get_context_window_status(),
            "system_health": self.get_system_health(),
        }

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health indicators"""
        health = {
            "status": "unknown",
            "database_size": 0,
            "log_files": 0,
            "last_activity": None,
            "issues": [],
        }

        # Database size
        if self.db_path.exists():
            health["database_size"] = self.db_path.stat().st_size

        # Count log files
        if self.logs_dir.exists():
            health["log_files"] = len(list(self.logs_dir.glob("*.log")))
        # Check for recent activity
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp FROM token_log ORDER BY timestamp DESC LIMIT 1"
            )
            result = cursor.fetchone()
            if result:
                health["last_activity"] = result[0]
            conn.close()
        except sqlite3.Error as e:
            health["issues"].append(f"Database error: {str(e)}")
        
        # Determine overall status
        active_agents = len(self.get_active_agents())
        if active_agents > 0:
            health["status"] = "active"
        elif health["last_activity"]:
            try:
                last_time = datetime.fromisoformat(
                    health["last_activity"].replace("Z", "")
                )
                if (datetime.utcnow() - last_time) < timedelta(hours=1):
                    health["status"] = "idle"
                else:
                    health["status"] = "inactive"
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing activity timestamp: {str(e)}")
                health["status"] = "unknown"
                health["issues"].append("Invalid timestamp format")
        else:
            health["status"] = "offline"

        return health

    def _get_status_indicator(self, status: str) -> str:
        """Get a status indicator based on status value"""
        indicators = {
            "optimal": "[OK]",
            "warning": "[WARN]",
            "critical": "[CRIT]",
            "error": "[ERR]",
            "unknown": "[???]"
        }
        return indicators.get(status.lower(), "[???]")

    def _format_usage_line(self, model: str, data: dict[str, Any]) -> str:
        """Format a usage statistics line with proper indicators"""
        status_indicator = self._get_status_indicator(data["status"])
        return (
            f"         {model}: {data['used']:,}/{data['limit']:,} tokens "
            f"({data['percent_used']:.1f}%) {status_indicator}"
        )

    def _display_model_usage(self) -> None:
        """Display model-specific usage details"""
        usage = self.get_token_usage_stats()
        
        for model, data in usage.items():
            if isinstance(data, dict) and "used" in data and "limit" in data:
                print(self._format_usage_line(model, data))
            elif model == "error":
                print(f"[ERROR] Failed to retrieve usage stats: {data}")
                if "details" in usage:
                    print(f"         Details: {usage['details']}")

    def display_usage_summary(self) -> None:
        """Display formatted usage summary"""
        print("\n=== KOR'TANA SYSTEM USAGE ===")
        print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        self._display_model_usage()
        print("\n" + "=" * 80)

    def print_dashboard(self):
        """Print comprehensive monitoring dashboard"""
        dashboard = self.get_dashboard_data()

        print("\n" + "=" * 80)
        print("               KOR'TANA ENHANCED SYSTEM DASHBOARD")
        print("=" * 80)
        print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        # System Health
        health = dashboard["system_health"]
        status_colors = {
            "active": "[ACTIVE]",
            "idle": "[IDLE]",
            "inactive": "[INACTIVE]",
            "offline": "[OFFLINE]",
            "unknown": "[UNKNOWN]",
        }
        print(
            f"\n[HEALTH] System Status: {status_colors.get(health['status'], '[UNKNOWN]')} {health['status'].upper()}"
        )
        print(f"         Database Size: {health['database_size']:,} bytes")
        print(f"         Log Files: {health['log_files']}")
        if health["last_activity"]:
            print(f"         Last Activity: {health['last_activity']}")

        # Active Agents
        agents = dashboard["active_agents"]
        print(f"\n[AGENTS] Active Agents: {len(agents)}")
        if agents:
            print(f"         Agents: {', '.join(agents)}")
        else:
            print("         No active agents detected")

        # Token Usage
        token_stats = dashboard["token_usage"]
        print("\n[TOKENS] Token Usage (Last 24h):")
        if token_stats["last_24h"]:
            for stage, tokens in token_stats["last_24h"].items():
                print(f"         {stage}: {tokens:,} tokens")
        else:
            print("         No token usage recorded")

        print(f"         Total Today: {token_stats['total_today']:,} tokens")

        # Rate Limits
        rate_limits = dashboard["rate_limits"]
        print("\n[LIMITS] Rate Limit Status:")
        for service, data in rate_limits.items():
            if service == "error":
                continue
            print(f"         {data['name']}:")
            if "tpm_limit" in data:
                print(
                    f"           TPM: {data['used_tokens']:,}/{data['tpm_limit']:,} ({data['tpm_percent']:.1f}%)"
                )
            if "rpm_limit" in data:
                print(
                    f"           RPM: {data['used_requests']}/{data['rpm_limit']} ({data['rpm_percent']:.1f}%)"
                )
            if "requests_limit" in data:
                print(
                    f"           Daily: {data['used_requests']}/{data['requests_limit']} ({data['requests_percent']:.1f}%)"
                )

        # Context Windows
        context_windows = dashboard["context_windows"]
        print("\n[CONTEXT] Context Window Status:")
        for model, data in context_windows.items():
            status_indicator = (
                "[OK]"
                if data["status"] == "optimal"
                else "[WARN]"
                if data["status"] == "warning"
                else "[CRIT]"
            )
            print(
                f"         {model}: {data['used']:,}/{data['limit']:,} tokens ({data['percent_used']:.1f}%) {status_indicator}"
            )

        print("\n" + "=" * 80)

    def monitor_loop(self, interval: int = 300):
        """Run continuous monitoring loop (default 5 minutes)"""
        print("[MONITOR] Starting enhanced monitoring dashboard...")
        print(f"[MONITOR] Refreshing every {interval} seconds")
        print("[MONITOR] Press Ctrl+C to stop")

        try:
            while True:
                # Clear screen (Windows)
                os.system("cls" if os.name == "nt" else "clear")
                self.print_dashboard()

                print(
                    f"\n[MONITOR] Next refresh in {interval} seconds... (Ctrl+C to stop)"
                )
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n[MONITOR] Monitoring stopped by user")


def main():
    """Main monitoring interface"""
    import sys

    monitor = KortanaEnhancedMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "--loop":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 300
            monitor.monitor_loop(interval)
        elif command == "--log-test":
            # Simulate logging for testing
            monitor.log_token_usage("dialogue_parser_001", "init", 25500, "claude")
            monitor.log_token_usage("dialogue_parser_001", "summarize", 52200, "gemini")
            monitor.log_chain_communication(
                "dialogue_parser_001", "handoff", 1200, "claude", "weaver"
            )
            print("[TEST] Sample data logged to database")
        elif command == "--dashboard":
            monitor.print_dashboard()
        else:
            print("Usage: python monitor.py [--dashboard|--loop [interval]|--log-test]")
    else:
        # Default: single dashboard view
        monitor.print_dashboard()


if __name__ == "__main__":
    main()
