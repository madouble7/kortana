#!/usr/bin/env python3
"""
KOR'TANA Autonomous Development Monitor
Real-time dashboard for monitoring autonomous development progress
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

# Configuration
BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
REFRESH_INTERVAL = int(os.getenv("MONITOR_REFRESH_INTERVAL", "5"))  # seconds
SHOW_DETAILED_LOGS = os.getenv("SHOW_DETAILED_LOGS", "false").lower() == "true"


class AutonomousMonitor:
    """Real-time monitoring dashboard for autonomous development"""

    def __init__(self, backend_url: str = BACKEND_URL):
        self.backend_url = backend_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.last_stats = None
        self.start_time = self._get_utc_now()
    
    def _get_utc_now(self) -> datetime:
        """Get current UTC time in a version-compatible way"""
        try:
            return datetime.now(timezone.utc)
        except AttributeError:
            # Python < 3.11 compatibility
            return datetime.utcnow().replace(tzinfo=timezone.utc)

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def print_header(self):
        """Print dashboard header"""
        now = self._get_utc_now()
        uptime = (now - self.start_time).total_seconds()
        print("=" * 80)
        print("🤖 KOR'TANA - AUTONOMOUS DEVELOPMENT MONITOR")
        print("=" * 80)
        print(f"🕐 Monitoring Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"⏱️  Uptime: {self.format_duration(uptime)}")
        print(f"🔗 Backend URL: {self.backend_url}")
        print(f"🔄 Refresh Rate: {REFRESH_INTERVAL}s")
        print("=" * 80)
        print()

    async def get_health(self) -> Dict[str, Any]:
        """Get backend health status"""
        try:
            response = await self.client.get(f"{self.backend_url}/api/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_hop_status(self) -> Dict[str, Any]:
        """Get Human Only Protocol status"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/autonomy/hop/protocol/status"
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_autonomy_status(self) -> Dict[str, Any]:
        """Get autonomy system status"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/api/autonomy/status"
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def run_hop_cycle(self) -> Dict[str, Any]:
        """Trigger an autonomous HOP cycle"""
        try:
            response = await self.client.post(
                f"{self.backend_url}/api/autonomy/hop/protocol/auto/cycle"
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def print_health_status(self, health: Dict[str, Any]):
        """Print health status section"""
        print("📊 SYSTEM HEALTH")
        print("-" * 80)
        
        if "error" in health:
            print(f"❌ Backend: OFFLINE - {health['error']}")
        else:
            status = health.get("status", "unknown")
            env = health.get("environment", "unknown")
            version = health.get("version", "unknown")
            
            if status == "alive":
                print(f"✅ Backend: ONLINE")
            else:
                print(f"⚠️  Backend: {status.upper()}")
            
            print(f"   Environment: {env}")
            print(f"   Version: {version}")
        print()

    def print_hop_status(self, hop_status: Dict[str, Any]):
        """Print Human Only Protocol status"""
        print("🧠 HUMAN ONLY PROTOCOL (HOP)")
        print("-" * 80)
        
        if "error" in hop_status:
            print(f"❌ HOP Status: UNAVAILABLE - {hop_status['error']}")
            print()
            return

        summary = hop_status.get("summary", {})
        classifications = hop_status.get("classifications", {})
        
        print(f"📈 Overall Progress:")
        print(f"   Total Tasks: {summary.get('total_tasks', 0)}")
        print(f"   ✅ Completed: {summary.get('completed', 0)}")
        print(f"   🔄 In Progress: {summary.get('in_progress', 0)}")
        print(f"   ⏳ Pending: {summary.get('pending', 0)}")
        print(f"   ❌ Failed: {summary.get('failed', 0)}")
        print(f"   ⏸️  Waiting for HO: {summary.get('waiting_for_ho', 0)}")
        print()

        # AUTO tasks
        auto = classifications.get("auto", {})
        auto_count = auto.get("count", 0)
        auto_total = auto.get("total", 0)
        auto_progress = (auto_count / auto_total * 100) if auto_total > 0 else 0
        print(f"🤖 AUTO Tasks: {auto_count}/{auto_total} ({auto_progress:.1f}%)")
        
        if SHOW_DETAILED_LOGS:
            auto_tasks = auto.get("tasks", [])
            for task in auto_tasks[:5]:  # Show first 5
                status_icon = "✅" if task.get("status") == "completed" else "⏳"
                print(f"   {status_icon} {task.get('name')}: {task.get('status')}")
        
        # HO tasks
        ho = classifications.get("ho", {})
        ho_count = ho.get("count", 0)
        ho_total = ho.get("total", 0)
        ho_progress = (ho_count / ho_total * 100) if ho_total > 0 else 0
        print(f"👤 HO Tasks: {ho_count}/{ho_total} ({ho_progress:.1f}%)")
        
        pending_ho = ho.get("pending", [])
        if pending_ho:
            print(f"   ⚠️  {len(pending_ho)} pending human actions:")
            for task in pending_ho[:3]:  # Show first 3
                print(f"      • {task.get('name')}")
        
        # Approval tasks
        approval = classifications.get("approval", {})
        approval_count = approval.get("count", 0)
        approval_total = approval.get("total", 0)
        ready = approval.get("ready", [])
        print(f"🔐 Approval Tasks: {approval_count}/{approval_total}")
        if ready:
            print(f"   🟢 {len(ready)} ready for approval:")
            for task in ready[:3]:  # Show first 3
                print(f"      • {task.get('name')}")
        
        print()

    def print_autonomy_status(self, autonomy: Dict[str, Any]):
        """Print autonomy system status"""
        print("⚙️  AUTONOMY SYSTEM")
        print("-" * 80)
        
        if "error" in autonomy:
            print(f"❌ Autonomy: UNAVAILABLE - {autonomy['error']}")
        else:
            print(f"✅ Autonomy Engine: ACTIVE")
            
            if "tasks" in autonomy:
                tasks = autonomy["tasks"]
                print(f"   📋 Active Tasks: {len(tasks)}")
                
                if SHOW_DETAILED_LOGS and tasks:
                    for task in tasks[:5]:
                        print(f"      • {task.get('title', 'Unknown')}")
        
        print()

    def print_instructions(self):
        """Print usage instructions"""
        print("⌨️  CONTROLS")
        print("-" * 80)
        print("   Ctrl+C : Stop monitoring")
        print("   The monitor auto-refreshes every {}s".format(REFRESH_INTERVAL))
        print()

    async def display_dashboard(self):
        """Display the full monitoring dashboard"""
        self.clear_screen()
        self.print_header()
        
        # Fetch all status data
        health = await self.get_health()
        hop_status = await self.get_hop_status()
        autonomy_status = await self.get_autonomy_status()
        
        # Display sections
        self.print_health_status(health)
        self.print_hop_status(hop_status)
        self.print_autonomy_status(autonomy_status)
        self.print_instructions()
        
        now = self._get_utc_now()
        print(f"⏰ Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    async def start_monitoring(self):
        """Start the monitoring loop"""
        print("🚀 Starting KOR'TANA Autonomous Development Monitor...")
        print(f"📡 Connecting to {self.backend_url}...")
        print()
        
        try:
            # Initial health check
            health = await self.get_health()
            if "error" in health:
                print(f"❌ Cannot connect to backend at {self.backend_url}")
                print(f"   Error: {health['error']}")
                print()
                print("💡 Make sure the backend is running:")
                print("   cd /home/runner/work/kortana/kortana")
                print("   docker compose up -d")
                print()
                return
            
            print("✅ Connected successfully!")
            print()
            time.sleep(2)
            
            # Main monitoring loop
            while True:
                await self.display_dashboard()
                await asyncio.sleep(REFRESH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n")
            print("=" * 80)
            print("🛑 Monitoring stopped by user")
            print("=" * 80)
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            await self.client.aclose()

    async def quick_status(self):
        """Display a quick status snapshot (non-looping)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client
            try:
                health = await self.get_health()
                hop_status = await self.get_hop_status()
                
                print("=" * 80)
                print("📊 KOR'TANA QUICK STATUS")
                print("=" * 80)
                print()
                
                self.print_health_status(health)
                self.print_hop_status(hop_status)
            finally:
                pass  # Client cleanup handled by context manager

    async def trigger_cycle(self):
        """Trigger one autonomous cycle and show results"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            self.client = client
            try:
                print("🔄 Triggering autonomous HOP cycle...")
                print()
                
                result = await self.run_hop_cycle()
                
                if "error" in result:
                    print(f"❌ Cycle failed: {result['error']}")
                else:
                    print("✅ Cycle completed!")
                    print()
                    print(f"Executed: {len(result.get('executed', []))}")
                    print(f"Failed: {len(result.get('failed', []))}")
                    
                    if result.get("pending_ho"):
                        print(f"⚠️  Human action required:")
                        ho = result["pending_ho"]
                        print(f"   Task: {ho.get('name')}")
                        print()
                        if ho.get('scaffold'):
                            print("📋 HO Scaffold:")
                            print(ho['scaffold'])
            
            finally:
                pass  # Client cleanup handled by context manager


async def main():
    """Main entry point"""
    monitor = AutonomousMonitor()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            await monitor.quick_status()
        elif command == "cycle":
            await monitor.trigger_cycle()
        elif command == "help":
            print("KOR'TANA Autonomous Development Monitor")
            print()
            print("Usage:")
            print("  python monitor_autonomous_dev.py         Start continuous monitoring")
            print("  python monitor_autonomous_dev.py status  Show quick status snapshot")
            print("  python monitor_autonomous_dev.py cycle   Trigger one autonomous cycle")
            print("  python monitor_autonomous_dev.py help    Show this help")
            print()
            print("Environment Variables:")
            print("  KORTANA_BACKEND_URL         Backend URL (default: http://localhost:8000)")
            print("  MONITOR_REFRESH_INTERVAL    Refresh interval in seconds (default: 5)")
            print("  SHOW_DETAILED_LOGS          Show detailed logs (default: false)")
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' to see available commands")
    else:
        # Default: start continuous monitoring
        await monitor.start_monitoring()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
