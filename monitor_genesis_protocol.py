#!/usr/bin/env python3
"""
Genesis Protocol Real-time Monitor
Tracks the autonomous execution progress
"""

import time
from datetime import datetime

import requests


def monitor_genesis_protocol():
    """Monitor the Genesis Protocol execution in real-time"""
    print("🎯 GENESIS PROTOCOL MONITOR")
    print("=" * 60)
    print("Monitoring autonomous execution progress...")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)

    last_status = None
    last_goal_count = 0

    try:
        while True:
            try:
                # Check server status
                response = requests.get("http://127.0.0.1:8000/", timeout=5)
                if response.status_code != 200:
                    print(f"⚠️  Server not responding properly: {response.status_code}")
                    time.sleep(10)
                    continue

                # Get current goals
                goals_response = requests.get("http://127.0.0.1:8000/goals/", timeout=5)
                if goals_response.status_code == 200:
                    goals = goals_response.json()

                    # Check for new goals
                    if len(goals) != last_goal_count:
                        print(f"\n📊 Goals Update: {len(goals)} total goals")
                        last_goal_count = len(goals)

                    # Monitor active goals
                    active_goals = [g for g in goals if g.get('status') == 'ACTIVE']
                    completed_goals = [g for g in goals if g.get('status') == 'COMPLETED']
                    failed_goals = [g for g in goals if g.get('status') == 'FAILED']

                    current_status = {
                        'active': len(active_goals),
                        'completed': len(completed_goals),
                        'failed': len(failed_goals),
                        'total': len(goals)
                    }

                    if current_status != last_status:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"\n[{timestamp}] 📈 Status Update:")
                        print(f"  🎯 Active: {current_status['active']}")
                        print(f"  ✅ Completed: {current_status['completed']}")
                        print(f"  ❌ Failed: {current_status['failed']}")
                        print(f"  📊 Total: {current_status['total']}")

                        # Show details for active goals
                        if active_goals:
                            print("\n🔄 Active Goals:")
                            for goal in active_goals:
                                goal_id = goal.get('id', 'Unknown')
                                description = goal.get('description', 'No description')[:80] + "..."
                                print(f"  • Goal {goal_id}: {description}")

                        last_status = current_status

                else:
                    print(f"❌ Failed to fetch goals: {goals_response.status_code}")

                # Wait before next check
                time.sleep(5)

            except requests.exceptions.ConnectionError:
                print("❌ Connection lost - Server may be down")
                time.sleep(10)
            except requests.exceptions.Timeout:
                print("⏰ Request timeout - Server may be busy")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
        print("=" * 60)


if __name__ == "__main__":
    monitor_genesis_protocol()
