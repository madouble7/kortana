#!/usr/bin/env python3
"""
Active daemon cycle monitor - polls every 30 seconds until issue #11000 has commit_sha and pr_number.
Provides real-time feedback as daemon executes.
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path


def get_issue_status():
    """Query issue #11000 from database."""
    db_path = Path("backend/github_tasks.db")
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, status, code_changes, commit_sha, github_pr_number,
                   error_message, error_count, executed_at, updated_at
            FROM github_tasks
            WHERE id = '11000'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


def format_status(issue):
    """Format issue status for display."""
    if not issue:
        return "❌ Issue #11000 not found"

    status = issue.get("status", "unknown")
    code_changes = "✓" if issue.get("code_changes") else "✗"
    commit_sha = issue.get("commit_sha", "NOT SET")
    pr_number = issue.get("github_pr_number", "NOT SET")
    error = issue.get("error_message")
    executed = issue.get("executed_at")

    lines = [
        f"Issue #11000 Status: {status}",
        f"  Code changes populated: {code_changes}",
        f"  Commit SHA: {commit_sha[:12]}" if commit_sha != "NOT SET" else "  Commit SHA: NOT SET",
        f"  PR Number: {pr_number}",
    ]

    if error:
        lines.append(f"  Error: {error}")

    if executed:
        lines.append(f"  Executed at: {executed}")

    lines.append(f"  Status updated at: {issue.get('updated_at')}")

    return "\n".join(lines)


def main():
    """Poll daemon status every 30 seconds until success or error."""
    print("🚀 Daemon Cycle Monitor Started")
    print("   Polling every 30 seconds until issue #11000 executes...")
    print("   Success = commit_sha + github_pr_number both populated\n")

    start_time = time.time()
    last_status = None
    check_count = 0

    while True:
        check_count += 1
        current_status = get_issue_status()
        elapsed = int(time.time() - start_time)

        # Only print if status changed
        if current_status != last_status:
            print(f"\n[{datetime.now().isoformat()}] Check #{check_count} (elapsed {elapsed}s)")
            print(format_status(current_status))
            last_status = current_status

            # Check for success
            if (
                current_status
                and current_status.get("commit_sha")
                and current_status.get("github_pr_number")
            ):
                print("\n✅ SUCCESS! Daemon executed issue #11000")
                print(f"   Commit SHA: {current_status['commit_sha']}")
                print(f"   PR Number: {current_status['github_pr_number']}")
                print(f"   Total elapsed: {elapsed}s ({elapsed // 60}m {elapsed % 60}s)")
                break

            # Check for persistent error
            if current_status and current_status.get("error_message"):
                error_count = current_status.get("error_count", 0)
                if error_count > 2:
                    print(
                        f"\n❌ ERROR after {error_count} attempts: {current_status['error_message']}"
                    )
                    print("   Stopping monitor")
                    break

        # Show progress every 2 minutes
        if check_count % 4 == 0:
            print(f"⏳ Still waiting... ({elapsed // 60}m {elapsed % 60}s)")

        # Timeout after 15 minutes
        if elapsed > 900:
            print(f"\n⏱️ Timeout after {elapsed // 60}m - daemon may be on extended cycle")
            print("   You can continue monitoring with: python monitor_issue_11000.py")
            break

        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitor stopped by user")
