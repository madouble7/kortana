#!/usr/bin/env python3
"""
Quick Autonomy Check - Is Kor'tana Working?
==========================================
Simple, immediate verification of autonomous activity
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(r"C:\project-kortana")

def quick_autonomy_check():
    """Quick check to see if Kor'tana is working autonomously."""

    print("🕵️ QUICK AUTONOMY CHECK")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Server Health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            print("✅ Server: ONLINE")
        else:
            print(f"⚠️  Server: Responding but status {response.status_code}")
    except:
        print("❌ Server: OFFLINE")
        print("   Start with: python -m uvicorn src.kortana.main:app --port 8000 --reload")
        return

    # 2. Goal Activity
    try:
        response = requests.get(f"{BASE_URL}/goals", timeout=5)
        if response.status_code == 200:
            goals = response.json()
            active = [g for g in goals if g.get('status') == 'ACTIVE']
            completed = [g for g in goals if g.get('status') == 'COMPLETED']
            pending = [g for g in goals if g.get('status') == 'PENDING']

            print(f"📋 Goals: {len(goals)} total")

            if active:
                print(f"   🔥 {len(active)} ACTIVE (Working now!)")
                for goal in active:
                    print(f"      → {goal.get('description', '')[:40]}...")

            if completed:
                print(f"   ✅ {len(completed)} COMPLETED (Autonomous work done)")

            if pending:
                print(f"   ⏳ {len(pending)} PENDING (Waiting for pickup)")

            if not goals:
                print("   📝 No goals - Submit one to see autonomous work!")

        else:
            print(f"⚠️  Goals API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Goals check failed: {e}")

    # 3. Memory Development
    try:
        response = requests.get(f"{BASE_URL}/memories", timeout=5)
        if response.status_code == 200:
            memories = response.json()
            core_beliefs = [m for m in memories if m.get('memory_type') == 'CORE_BELIEF']
            observations = [m for m in memories if m.get('memory_type') == 'OBSERVATION']

            print(f"🧠 Memories: {len(memories)} total")
            print(f"   🎯 {len(core_beliefs)} Core Beliefs (Learning)")
            print(f"   👁️  {len(observations)} Observations (Experience)")

            if core_beliefs:
                print("   Latest belief:")
                latest = sorted(core_beliefs, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                print(f"      → {latest.get('content', '')[:50]}...")

        else:
            print(f"⚠️  Memory API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Memory check failed: {e}")

    # 4. File System Activity
    autonomous_logs = PROJECT_ROOT / "data" / "autonomous_logs"
    if autonomous_logs.exists():
        log_files = list(autonomous_logs.glob("*.log"))
        if log_files:
            print(f"📁 Log files: {len(log_files)} found")
            for log_file in log_files:
                size = log_file.stat().st_size
                if size > 0:
                    print(f"   📝 {log_file.name}: {size} bytes (Has activity)")
                else:
                    print(f"   📝 {log_file.name}: Empty")
        else:
            print("📁 No autonomous log files found")
    else:
        print("📁 Autonomous logs directory not found")

    # 5. Status Files
    status_file = PROJECT_ROOT / "data" / "autonomous_status.json"
    if status_file.exists():
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)

            if status:
                print(f"🤖 System status: {status.get('status', 'unknown')}")
                if 'current_goal_id' in status:
                    print(f"   Working on Goal: {status['current_goal_id']}")
                if 'reasoning_cycles' in status:
                    print(f"   Reasoning cycles: {status['reasoning_cycles']}")
            else:
                print("🤖 Status file empty")
        except:
            print("🤖 Status file unreadable")
    else:
        print("🤖 No status file found")

    print()
    print("=" * 50)
    print("🎯 AUTONOMY ASSESSMENT:")

    # Simple autonomy indicators
    indicators = []

    # Check if any goals are active
    try:
        response = requests.get(f"{BASE_URL}/goals", timeout=3)
        if response.status_code == 200:
            goals = response.json()
            if any(g.get('status') == 'ACTIVE' for g in goals):
                indicators.append("🔥 Currently executing tasks")
            if any(g.get('status') == 'COMPLETED' for g in goals):
                indicators.append("✅ Has completed autonomous work")
    except:
        pass

    # Check if memories exist
    try:
        response = requests.get(f"{BASE_URL}/memories", timeout=3)
        if response.status_code == 200:
            memories = response.json()
            if memories:
                indicators.append("🧠 Has formed memories")
    except:
        pass

    # Check if logs have content
    if autonomous_logs.exists():
        for log_file in autonomous_logs.glob("*.log"):
            if log_file.stat().st_size > 100:  # More than trivial content
                indicators.append("📝 Generating autonomous logs")
                break

    if indicators:
        print("✅ AUTONOMOUS ACTIVITY DETECTED:")
        for indicator in indicators:
            print(f"   {indicator}")
        print("\n🎉 Kor'tana appears to be working autonomously!")
    else:
        print("😴 NO CLEAR AUTONOMOUS ACTIVITY")
        print("   Consider:")
        print("   1. Submit a goal: python launch_proving_ground_fixed.py")
        print("   2. Check server logs for autonomous cycles")
        print("   3. Wait a few minutes and check again")

    print("\n📊 For detailed monitoring, run:")
    print("   python monitor_autonomous_activity.py")

if __name__ == "__main__":
    quick_autonomy_check()
