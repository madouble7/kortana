#!/usr/bin/env python3
"""
🔍 PROACTIVE ENGINEER VALIDATION
Check if Kor'tana's proactive code scanning is working
"""

import sqlite3
from pathlib import Path


def check_proactive_status():
    """Check the current status of proactive engineering."""

    print("🔍 PROACTIVE ENGINEER STATUS CHECK")
    print("=" * 50)

    # Check database goals
    try:
        db_path = Path("kortana.db")
        if not db_path.exists():
            print("❌ Database file not found")
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check goals table
        cursor.execute("SELECT COUNT(*) FROM goals")
        total_goals = cursor.fetchone()[0]
        print(f"📊 Total goals in database: {total_goals}")

        # Check recent goals
        cursor.execute(
            "SELECT id, description, status, created_at FROM goals ORDER BY id DESC LIMIT 5"
        )
        recent_goals = cursor.fetchall()

        print("\n📋 Recent Goals:")
        for goal in recent_goals:
            print(f"   Goal {goal[0]}: {goal[1][:60]}...")
            print(f"   Status: {goal[2]} | Created: {goal[3]}")
            print()

        # Check for proactive goals (created by code scanner)
        cursor.execute(
            "SELECT COUNT(*) FROM goals WHERE description LIKE '%docstring%' OR description LIKE '%proactive%'"
        )
        proactive_count = cursor.fetchone()[0]
        print(f"🤖 Proactive goals detected: {proactive_count}")

        conn.close()

    except Exception as e:
        print(f"❌ Database error: {e}")

    # Check if proactive task is in autonomous tasks
    try:
        print("\n🔧 Checking autonomous tasks configuration...")
        from src.kortana.core.autonomous_tasks import run_proactive_code_review_task

        print("✅ Proactive code review task found")
    except ImportError as e:
        print(f"❌ Proactive task not found: {e}")

    # Test code scanner directly
    try:
        print("\n🔍 Testing code scanner directly...")
        from src.kortana.config import load_config
        from src.kortana.core.execution_engine import ExecutionEngine

        config = load_config()
        engine = ExecutionEngine(config)

        # Test scan
        result = engine.scan_codebase_for_issues(
            "src/kortana/api/routers", ["missing_docstrings"]
        )
        print(f"✅ Code scanner test: Found {len(result.get('issues', []))} issues")

        if result.get("issues"):
            print("📝 Sample issues found:")
            for issue in result["issues"][:3]:
                print(f"   - {issue}")

    except Exception as e:
        print(f"❌ Code scanner test failed: {e}")


if __name__ == "__main__":
    check_proactive_status()
