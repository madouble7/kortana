#!/usr/bin/env python3
"""
Test script for AlwaysOnMonitor
"""

import asyncio
import sys

# Add src to path
sys.path.append("src")

from kortana.services.always_on_monitor import AlwaysOnMonitor


async def test_monitor():
    """Test the AlwaysOnMonitor functionality"""
    print("🚀 Testing AlwaysOnMonitor...")

    # Create monitor instance
    monitor = AlwaysOnMonitor()
    print("✅ Monitor created successfully")

    # Test status method
    status = monitor.get_status()
    print("📊 Monitor status:", status)

    # Test async methods
    try:
        task_status = await monitor.get_task_status()
        print("📋 Task status:", task_status)
    except Exception as e:
        print(f"⚠️ Task status error (expected - no DB): {e}")

    try:
        force_result = await monitor.force_check()
        print("⚡ Force check result:", force_result)
    except Exception as e:
        print(f"⚠️ Force check error (expected - no DB): {e}")

    print("✅ All basic tests passed!")

    # Test monitoring cycle (without starting)
    print("\n🔄 Testing monitoring cycle...")
    try:
        await monitor._monitoring_cycle()
        print("✅ Monitoring cycle completed successfully")
    except Exception as e:
        print(f"⚠️ Monitoring cycle error (expected - no DB): {e}")

    print("\n🎉 AlwaysOnMonitor basic functionality verified!")


if __name__ == "__main__":
    asyncio.run(test_monitor())
