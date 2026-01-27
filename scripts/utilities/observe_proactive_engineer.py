#!/usr/bin/env python3
"""
🚀 BATCH 10 PHASE 2 OBSERVER: The Proactive Engineer Initiative

This script monitors Kor'tana's proactive engineering behavior by:
1. Checking the Goals API for self-generated goals
2. Monitoring autonomous activity logs
3. Observing the execution of proactive code review tasks
4. Validating that Kor'tana is truly autonomous in identifying and addressing issues

Run this to verify that Kor'tana is operating as a fully autonomous software engineer.
"""

import asyncio
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("proactive_engineer_observation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = "sqlite:///kortana.db"


def print_header():
    """Print a beautiful header for the observation session."""
    print("\n" + "=" * 80)
    print("🚀 BATCH 10: THE PROACTIVE ENGINEER INITIATIVE - OBSERVATION SESSION")
    print("=" * 80)
    print("🔍 Monitoring Kor'tana's autonomous engineering capabilities...")
    print("⚡ Looking for self-generated goals and proactive behaviors")
    print("🧠 Validating true software engineering autonomy")
    print("=" * 80 + "\n")


def check_api_health():
    """Check if the Kor'tana API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Kor'tana API is running and responsive")
            return True
        else:
            logger.warning(f"⚠️ API returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to Kor'tana API: {e}")
        return False


def get_recent_goals():
    """Fetch recent goals from the API to analyze autonomous behavior."""
    try:
        response = requests.get(f"{API_BASE_URL}/goals", timeout=10)
        if response.status_code == 200:
            goals = response.json()
            logger.info(f"📊 Retrieved {len(goals)} total goals from API")

            # Filter for proactive goals created in the last 24 hours
            now = datetime.now(UTC)
            recent_cutoff = now - timedelta(hours=24)

            proactive_goals = []
            recent_goals = []

            for goal in goals:
                # Parse the created_at timestamp
                try:
                    created_at = datetime.fromisoformat(
                        goal.get("created_at", "").replace("Z", "+00:00")
                    )
                    if created_at > recent_cutoff:
                        recent_goals.append(goal)

                        # Check if this is a proactive goal
                        metadata = goal.get("metadata", {})
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)

                        if metadata.get("type") == "proactive_code_quality":
                            proactive_goals.append(goal)
                except Exception as e:
                    logger.warning(f"Could not parse goal timestamp: {e}")
                    continue

            return {
                "total_goals": len(goals),
                "recent_goals": recent_goals,
                "proactive_goals": proactive_goals,
            }
        else:
            logger.error(f"Failed to fetch goals: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching goals: {e}")
        return None


def analyze_proactive_behavior(goal_data):
    """Analyze the goals to determine autonomous behavior patterns."""
    if not goal_data:
        logger.warning("No goal data available for analysis")
        return

    print("\n📊 PROACTIVE BEHAVIOR ANALYSIS")
    print("-" * 50)

    total = goal_data["total_goals"]
    recent = len(goal_data["recent_goals"])
    proactive = len(goal_data["proactive_goals"])

    print(f"📈 Total Goals in System: {total}")
    print(f"🕐 Recent Goals (24h): {recent}")
    print(f"🚀 Self-Generated Proactive Goals: {proactive}")

    if proactive > 0:
        print("\n✅ AUTONOMOUS ENGINEERING DETECTED!")
        print(
            f"🎯 Kor'tana has independently identified {proactive} code quality issues"
        )
        print("🧠 This demonstrates true proactive software engineering capabilities")

        print("\n📋 PROACTIVE GOALS DETAILS:")
        for i, goal in enumerate(goal_data["proactive_goals"], 1):
            metadata = goal.get("metadata", {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            print(f"\n  Goal {i}:")
            print(f"    📝 Description: {goal.get('description', 'N/A')[:100]}...")
            print(f"    📁 File: {metadata.get('file', 'N/A')}")
            print(f"    🔧 Function: {metadata.get('function', 'N/A')}")
            print(f"    🏷️ Issue Type: {metadata.get('issue_type', 'N/A')}")
            print(f"    ⚡ Status: {goal.get('status', 'N/A')}")
    else:
        print("\n⏳ NO PROACTIVE GOALS DETECTED YET")
        print("🔄 This could mean:")
        print("   • The proactive task hasn't run yet (runs every 2 hours)")
        print("   • The codebase is already well-documented")
        print("   • The proactive scanner is still initializing")


def check_autonomous_logs():
    """Check autonomous activity logs for proactive behavior."""
    log_file = Path("data/autonomous_activity.log")

    print("\n📂 AUTONOMOUS ACTIVITY LOG ANALYSIS")
    print("-" * 50)

    if log_file.exists():
        try:
            with open(log_file, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            total_lines = len(lines)

            # Look for proactive activity markers
            proactive_entries = [
                line
                for line in lines
                if "proactive" in line.lower() or "scan" in line.lower()
            ]

            print(f"📊 Log file found: {log_file}")
            print(f"📏 Total log lines: {total_lines}")
            print(f"🔍 Proactive activity entries: {len(proactive_entries)}")

            if proactive_entries:
                print("\n🚀 PROACTIVE ACTIVITY DETECTED:")
                for entry in proactive_entries[-5:]:  # Show last 5 entries
                    if entry.strip():
                        print(f"   {entry.strip()}")
            else:
                print("⏳ No proactive activity detected in logs yet")

        except Exception as e:
            logger.error(f"Error reading autonomous log: {e}")
    else:
        print(f"📂 No autonomous activity log found at {log_file}")
        print("⏳ This suggests the autonomous system hasn't activated yet")


def check_database_activity():
    """Check database for recent autonomous activity."""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        print("\n🗄️ DATABASE ACTIVITY ANALYSIS")
        print("-" * 50)

        # Check for recent core memories about proactive behavior
        query = text("""
            SELECT content, created_at, metadata
            FROM core_memories
            WHERE metadata LIKE '%proactive%'
               OR content LIKE '%proactive%'
               OR content LIKE '%scan%'
            ORDER BY created_at DESC
            LIMIT 5
        """)

        result = db.execute(query)
        memories = result.fetchall()

        print(f"🧠 Proactive memories found: {len(memories)}")

        for i, memory in enumerate(memories, 1):
            print(f"\n  Memory {i}:")
            print(f"    📝 Content: {memory[0][:100]}...")
            print(f"    🕐 Created: {memory[1]}")

        db.close()

    except Exception as e:
        logger.error(f"Error checking database: {e}")


def trigger_proactive_scan():
    """Manually trigger a proactive code review to test the system."""
    print("\n🔧 MANUAL PROACTIVE SCAN TRIGGER")
    print("-" * 50)

    try:
        # Import and run the proactive task directly
        import sys

        sys.path.append(".")

        from kortana.core.autonomous_tasks import run_proactive_code_review_task
        from kortana.services.database import get_db_sync

        db_gen = get_db_sync()
        db = next(db_gen)

        print("🚀 Running proactive code review task...")
        asyncio.run(run_proactive_code_review_task(db))

        db.close()
        print("✅ Proactive scan completed!")

    except Exception as e:
        logger.error(f"Error running manual proactive scan: {e}")
        print(f"❌ Manual scan failed: {e}")


async def continuous_observation(duration_minutes=30):
    """Continuously observe Kor'tana's behavior for a specified duration."""
    print("\n🕐 CONTINUOUS OBSERVATION MODE")
    print("-" * 50)
    print(f"⏰ Observing for {duration_minutes} minutes...")
    print("🔄 Checking every 2 minutes for new autonomous activity")

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    check_interval = 120  # 2 minutes

    observation_count = 0

    while time.time() < end_time:
        observation_count += 1
        elapsed_minutes = (time.time() - start_time) / 60

        print(
            f"\n🔍 OBSERVATION #{observation_count} (at {elapsed_minutes:.1f} minutes)"
        )
        print("━" * 40)

        # Quick health and goal check
        if check_api_health():
            goal_data = get_recent_goals()
            if goal_data and goal_data["proactive_goals"]:
                print(
                    f"🎉 BREAKTHROUGH: {len(goal_data['proactive_goals'])} proactive goals detected!"
                )
                analyze_proactive_behavior(goal_data)
                return  # Exit early if we detect proactive behavior

        remaining_minutes = (end_time - time.time()) / 60
        print(
            f"⏳ Next check in 2 minutes... ({remaining_minutes:.1f} minutes remaining)"
        )

        if remaining_minutes > 2:
            time.sleep(check_interval)
        else:
            time.sleep(remaining_minutes * 60)
            break

    print(f"\n⏰ Observation period complete after {duration_minutes} minutes")


def main():
    """Main observation function."""
    print_header()

    # Check if API is running
    if not check_api_health():
        print("💡 Starting the Kor'tana server might be needed first:")
        print("   Run: npm run dev -- --port 3010")
        print("   Or check if the server is running on a different port")
        return

    # Analyze current state
    print("🔍 INITIAL STATE ANALYSIS")
    print("=" * 50)

    goal_data = get_recent_goals()
    analyze_proactive_behavior(goal_data)
    check_autonomous_logs()
    check_database_activity()

    # Check if we already see proactive behavior
    if goal_data and goal_data["proactive_goals"]:
        print("\n🎉 SUCCESS: Proactive engineering behavior already detected!")
        print("✅ Kor'tana is operating as an autonomous software engineer")
        return

    print("\n🤔 No immediate proactive behavior detected.")
    print("This could be normal - let's investigate further...")

    # Offer to trigger a manual scan
    try:
        response = input(
            "\n❓ Would you like to trigger a manual proactive scan? (y/n): "
        )
        if response.lower().startswith("y"):
            trigger_proactive_scan()

            # Re-check after manual trigger
            print("\n🔄 Re-checking after manual trigger...")
            time.sleep(5)
            goal_data = get_recent_goals()
            analyze_proactive_behavior(goal_data)
    except KeyboardInterrupt:
        print("\n\n⏹️ Observation interrupted by user")
        return

    # Offer continuous observation
    try:
        response = input(
            "\n❓ Would you like to start continuous observation mode? (y/n): "
        )
        if response.lower().startswith("y"):
            asyncio.run(continuous_observation())
    except KeyboardInterrupt:
        print("\n\n⏹️ Observation interrupted by user")

    print("\n🏁 OBSERVATION SESSION COMPLETE")
    print("📋 Check the logs and goal API for ongoing autonomous activity")
    print("🚀 Kor'tana should continue proactive engineering in the background")


if __name__ == "__main__":
    main()
