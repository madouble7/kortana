#!/usr/bin/env python3
"""
Kor'tana Monitoring Dashboard
=============================
Real-time monitoring of the autonomous agent system
"""

import json
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


class KortanaMonitor:
    """Real-time monitoring dashboard for Kor'tana system"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent
        )
        self.db_path = self.project_root / "kortana.db"
        self.logs_dir = self.project_root / "logs"

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get current agent statistics"""
        stats = {
            "total_agents": 0,
            "active_agents": 0,
            "total_messages": 0,
            "agents": {},
        }

        # Scan log files
        if self.logs_dir.exists():
            log_files = list(self.logs_dir.glob("*.log"))
            stats["total_agents"] = len(log_files)

            for log_file in log_files:
                agent_name = log_file.stem
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # Count non-empty, non-comment lines
                    messages = [
                        line
                        for line in lines
                        if line.strip() and not line.startswith("//")
                    ]
                    message_count = len(messages)                    # Check if active (messages in last hour)
                    is_active = False
                    if lines:
                        try:
                            # Simple heuristic: if file was modified recently
                            modified_time = datetime.fromtimestamp(
                                log_file.stat().st_mtime
                            )
                            is_active = (datetime.now() - modified_time) < timedelta(
                                hours=1
                            )
                        except Exception:
                            pass

                    stats["agents"][agent_name] = {
                        "messages": message_count,
                        "active": is_active,
                        "last_modified": (
                            log_file.stat().st_mtime if log_file.exists() else 0
                        ),
                    }

                    stats["total_messages"] += message_count
                    if is_active:
                        stats["active_agents"] += 1

                except Exception as e:
                    stats["agents"][agent_name] = {
                        "messages": 0,
                        "active": False,
                        "error": str(e),
                    }

        return stats

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            "context_packages": 0,
            "total_tokens": 0,
            "recent_activity": [],
            "database_size": 0,
        }

        if not self.db_path.exists():
            return stats

        try:
            # Get file size
            stats["database_size"] = self.db_path.stat().st_size

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count context packages
            cursor.execute("SELECT COUNT(*), SUM(tokens) FROM context")
            count, total_tokens = cursor.fetchone()
            stats["context_packages"] = count or 0
            stats["total_tokens"] = total_tokens or 0

            # Get recent activity
            cursor.execute(
                """
                SELECT task_id, timestamp, tokens
                FROM context
                ORDER BY timestamp DESC
                LIMIT 5
            """
            )
            recent = cursor.fetchall()
            stats["recent_activity"] = [
                {"task_id": row[0], "timestamp": row[1], "tokens": row[2]}
                for row in recent
            ]

            conn.close()

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def get_torch_stats(self) -> Dict[str, Any]:
        """Get torch protocol statistics"""
        stats = {
            "total_torches": 0,
            "active_torches": 0,
            "recent_handoffs": [],
            "agent_lineage": [],
            "torch_chains": {},
            "error": None
        }

        try:
            if not self.db_path.exists():
                stats["error"] = "Database not found"
                return stats

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if torch tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'torch_%'")
            torch_tables = [row[0] for row in cursor.fetchall()]

            if not torch_tables:
                stats["error"] = "Torch tables not found - torch protocol not initialized"
                conn.close()
                return stats

            # Get total torch packages
            cursor.execute("SELECT COUNT(*) FROM torch_packages")
            stats["total_torches"] = cursor.fetchone()[0]

            # Get active torches
            cursor.execute("SELECT COUNT(*) FROM torch_packages WHERE status = 'active'")
            stats["active_torches"] = cursor.fetchone()[0]

            # Get recent handoffs
            cursor.execute("""
                SELECT torch_id, task_title, from_agent, to_agent, handoff_reason,
                       timestamp, tokens
                FROM torch_packages
                ORDER BY timestamp DESC
                LIMIT 10
            """)

            for row in cursor.fetchall():
                stats["recent_handoffs"].append({
                    "torch_id": row[0],
                    "task_title": row[1],
                    "from_agent": row[2],
                    "to_agent": row[3],
                    "handoff_reason": row[4],
                    "timestamp": row[5],
                    "tokens": row[6]
                })

            # Get agent lineage data
            cursor.execute("""
                SELECT tl.torch_id, tp.task_title, tl.agent_name, tl.timestamp,
                       tl.contribution_summary
                FROM torch_lineage tl
                JOIN torch_packages tp ON tl.torch_id = tp.torch_id
                ORDER BY tl.timestamp DESC
                LIMIT 20
            """)

            for row in cursor.fetchall():
                stats["agent_lineage"].append({
                    "torch_id": row[0],
                    "task_title": row[1],
                    "agent_name": row[2],
                    "timestamp": row[3],
                    "contribution": row[4]
                })

            # Analyze torch chains
            cursor.execute("""
                SELECT torch_id, COUNT(*) as chain_length
                FROM torch_lineage
                GROUP BY torch_id
                ORDER BY chain_length DESC
                LIMIT 5
            """)

            for row in cursor.fetchall():
                torch_id = row[0]
                chain_length = row[1]

                # Get chain details
                cursor.execute("""
                    SELECT agent_name, timestamp
                    FROM torch_lineage
                    WHERE torch_id = ?
                    ORDER BY sequence_number
                """, (torch_id,))

                chain_agents = [agent_row[0] for agent_row in cursor.fetchall()]
                stats["torch_chains"][torch_id] = {
                    "length": chain_length,
                    "agents": chain_agents
                }

            conn.close()

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health = {
            "status": "unknown",
            "uptime": "unknown",
            "last_cycle": "unknown",
            "issues": [],
        }

        # Check if relay state file exists
        state_file = self.project_root / "data" / "relay_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)

                # Find most recent activity
                most_recent = None
                for agent, info in state.items():
                    if isinstance(info, dict) and "last_processed_time" in info:
                        timestamp = info["last_processed_time"]
                        if not most_recent or timestamp > most_recent:
                            most_recent = timestamp

                if most_recent:
                    health["last_cycle"] = most_recent
                    # Check if recent (within last 10 minutes)
                    try:
                        last_time = datetime.fromisoformat(
                            most_recent.replace("Z", "+00:00")
                        )
                        time_diff = datetime.now() - last_time.replace(tzinfo=None)                        if time_diff < timedelta(minutes=10):
                            health["status"] = "active"
                        elif time_diff < timedelta(hours=1):
                            health["status"] = "idle"
                        else:
                            health["status"] = "inactive"
                            health["issues"].append("No recent activity")
                    except Exception:
                        health["status"] = "unknown"
                        health["issues"].append("Cannot parse timestamp")

            except Exception as e:
                health["issues"].append(f"State file error: {e}")
        else:
            health["issues"].append("No relay state file found")

        # Check for required files
        required_files = ["relays/relay.py", "kortana.db", "logs"]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                health["issues"].append(f"Missing: {file_path}")

        if not health["issues"] and health["status"] == "unknown":
            health["status"] = "ready"

        return health

    def print_dashboard(self):
        """Print monitoring dashboard"""
        print("\n" + "=" * 70)
        print("🤖 KOR'TANA AUTONOMOUS SYSTEM DASHBOARD")
        print("=" * 70)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # System Health
        health = self.get_system_health()
        status_emoji = {
            "active": "🟢",
            "idle": "🟡",
            "inactive": "🔴",
            "ready": "🟢",
            "unknown": "⚪",
        }

        print(
            f"\n🏥 SYSTEM HEALTH: {status_emoji.get(health['status'], '⚪')} {health['status'].upper()}"
        )
        if health["issues"]:
            print("   Issues:")
            for issue in health["issues"]:
                print(f"   - ⚠️ {issue}")
        if health["last_cycle"] != "unknown":
            print(f"   Last Activity: {health['last_cycle']}")

        # Agent Statistics
        agent_stats = self.get_agent_stats()
        print("\n🤖 AGENT NETWORK:")
        print(f"   Total Agents: {agent_stats['total_agents']}")
        print(f"   Active Agents: {agent_stats['active_agents']}")
        print(f"   Total Messages: {agent_stats['total_messages']}")

        print("\n   Agent Details:")
        for agent_name, info in agent_stats["agents"].items():
            status_icon = "🟢" if info["active"] else "⚪"
            print(
                f"   {status_icon} {agent_name:12} | {info['messages']:4} msgs | {'Active' if info['active'] else 'Idle'}"
            )

        # Database Statistics
        db_stats = self.get_database_stats()
        print("\n💾 DATABASE:")
        print(f"   Context Packages: {db_stats['context_packages']}")
        print(f"   Total Tokens: {db_stats['total_tokens']:,}")
        print(f"   Database Size: {db_stats['database_size']} bytes")

        if db_stats["recent_activity"]:
            print("\n   Recent Activity:")
            for activity in db_stats["recent_activity"][:3]:
                timestamp = (
                    activity["timestamp"][:19] if activity["timestamp"] else "unknown"
                )
                print(
                    f"   📦 {activity['task_id'][:20]:20} | {activity['tokens']:4} tokens | {timestamp}"
                )

        # Torch Protocol Statistics
        torch_stats = self.get_torch_stats()
        if not torch_stats.get("error"):
            print("\n🔥 TORCH PROTOCOL:")
            print(f"   Total Torches: {torch_stats['total_torches']}")
            print(f"   Active Torches: {torch_stats['active_torches']}")

            if torch_stats["recent_handoffs"]:
                print("\n   Recent Handoffs:")
                for handoff in torch_stats["recent_handoffs"][:3]:
                    timestamp = handoff["timestamp"][:19] if handoff["timestamp"] else "unknown"
                    print(f"   🔥 {handoff['from_agent']} → {handoff['to_agent']} | {timestamp}")

        print("\n" + "=" * 70)

    def print_torch_dashboard(self):
        """Print torch protocol specific dashboard"""
        print("\n🔥 TORCH PROTOCOL DASHBOARD")
        print("=" * 50)

        torch_stats = self.get_torch_stats()

        if torch_stats["error"]:
            print(f"❌ Error: {torch_stats['error']}")
            return

        print(f"🔥 Total Torch Packages: {torch_stats['total_torches']}")
        print(f"🔥 Active Torches: {torch_stats['active_torches']}")

        # Recent handoffs
        if torch_stats["recent_handoffs"]:
            print("\n📋 RECENT HANDOFFS:")
            for handoff in torch_stats["recent_handoffs"][:5]:
                timestamp = handoff["timestamp"][:19] if handoff["timestamp"] else "unknown"
                print(f"  🔥 {handoff['torch_id'][:8]}... | {handoff['from_agent']} → {handoff['to_agent']}")
                print(f"     Task: {handoff['task_title'][:40]}...")
                print(f"     Reason: {handoff['handoff_reason'][:50]}...")
                print(f"     Time: {timestamp} | Tokens: {handoff['tokens']:,}")
                print()

        # Torch chains
        if torch_stats["torch_chains"]:
            print("🔗 LONGEST TORCH CHAINS:")
            for torch_id, chain_info in torch_stats["torch_chains"].items():
                print(f"  🔥 {torch_id[:8]}... | Chain Length: {chain_info['length']}")
                print(f"     Agent Flow: {' → '.join(chain_info['agents'])}")
                print()

        # Agent lineage
        if torch_stats["agent_lineage"]:
            print("👥 RECENT AGENT CONTRIBUTIONS:")
            for contrib in torch_stats["agent_lineage"][:5]:
                timestamp = contrib["timestamp"][:19] if contrib["timestamp"] else "unknown"
                print(f"  📝 {contrib['agent_name']} | {timestamp}")
                print(f"     Task: {contrib['task_title'][:40]}...")
                print(f"     Contribution: {contrib['contribution'][:60]}...")
                print()

    def monitor_loop(self, interval: int = 30):
        """Run continuous monitoring loop"""
        print("🎛️ Starting Kor'tana monitoring dashboard...")
        print(f"📊 Refreshing every {interval} seconds")
        print("🛑 Press Ctrl+C to stop")

        try:
            while True:
                # Clear screen (Windows)
                os.system("cls" if os.name == "nt" else "clear")
                self.print_dashboard()

                print(f"\n⏱️ Next refresh in {interval} seconds... (Ctrl+C to stop)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")


def main():
    """Main monitoring interface"""
    monitor = KortanaMonitor()

    print("=" * 50)
    print(" KOR'TANA MONITORING DASHBOARD")
    print("=" * 50)

    print("\nOptions:")
    print("1. Single status check")
    print("2. Continuous monitoring")
    print("3. Agent details")
    print("4. Database analysis")
    print("5. Torch protocol analysis")
    print("0. Exit")

    choice = input("\nEnter choice (0-5): ").strip()

    if choice == "1":
        monitor.print_dashboard()
    elif choice == "2":
        interval = input("Refresh interval in seconds (default 30): ").strip()
        interval = int(interval) if interval.isdigit() else 30
        monitor.monitor_loop(interval)
    elif choice == "3":
        stats = monitor.get_agent_stats()
        print("\n🤖 DETAILED AGENT ANALYSIS:")
        print("=" * 40)
        for agent_name, info in stats["agents"].items():
            print(f"\n📋 Agent: {agent_name}")
            print(f"   Messages: {info['messages']}")
            print(f"   Status: {'Active' if info['active'] else 'Idle'}")
            if "error" in info:
                print(f"   Error: {info['error']}")
    elif choice == "4":
        stats = monitor.get_database_stats()
        print("\n💾 DATABASE ANALYSIS:")
        print("=" * 30)
        print(f"Context Packages: {stats['context_packages']}")
        print(f"Total Tokens: {stats['total_tokens']:,}")
        print(f"Database Size: {stats['database_size']} bytes")

        if stats["recent_activity"]:
            print("\nRecent Activity:")
            for activity in stats["recent_activity"]:
                print(
                    f"  {activity['task_id']} | {activity['tokens']} tokens | {activity['timestamp']}"
                )
    elif choice == "5":
        monitor.print_torch_dashboard()
    elif choice == "0":
        print("Monitoring session ended.")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
