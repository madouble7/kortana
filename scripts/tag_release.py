#!/usr/bin/env python
"""
Tag the current commit for release audit.

This script tags the current commit with a release tag.
"""

import argparse
import subprocess
import sys
from datetime import datetime


def color_print(message, color="green"):
    """Print colored messages to the console."""
    colors = {
        "reset": "\033[0m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stderr.strip(), e.returncode
    except Exception as e:
        return str(e), 1


def check_uncommitted_changes():
    """Check for uncommitted changes."""
    output, status = run_command(["git", "status", "--porcelain"], check=False)
    if output:
        color_print("⚠️ Warning: You have uncommitted changes:", "yellow")
        print(output)
        return True
    return False


def create_tag(tag_name, message=None):
    """Create a git tag."""
    cmd = ["git", "tag", "-a", tag_name]

    if message:
        cmd.extend(["-m", message])
    else:
        cmd.extend(["-m", f"Release tag {tag_name}"])

    output, status = run_command(cmd)
    if status != 0:
        color_print(f"❌ Failed to create tag: {output}", "red")
        return False

    color_print(f"✅ Tag '{tag_name}' created successfully", "green")
    return True


def push_tag(tag_name):
    """Push the tag to the remote repository."""
    output, status = run_command(["git", "push", "origin", tag_name])
    if status != 0:
        color_print(f"❌ Failed to push tag: {output}", "red")
        return False

    color_print(f"✅ Tag '{tag_name}' pushed to origin", "green")
    return True


def main():
    """Run the tag release script."""
    parser = argparse.ArgumentParser(
        description="Tag the current commit for release audit."
    )
    parser.add_argument("--tag", help="Tag name (default: audit-YYYY-MM-DD)")
    parser.add_argument("--message", help="Tag message (optional)")
    parser.add_argument(
        "--push", action="store_true", help="Push the tag to the remote repository"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Create tag even with uncommitted changes",
    )

    args = parser.parse_args()

    color_print("🔖 Tagging Release for Audit", "blue")
    print("==============================")

    # Check for uncommitted changes
    has_changes = check_uncommitted_changes()
    if has_changes and not args.force:
        color_print("❌ Aborting: You have uncommitted changes", "red")
        color_print("   Use --force to tag anyway", "yellow")
        return 1

    # Generate tag name if not provided
    tag_name = args.tag
    if not tag_name:
        tag_name = f"audit-{datetime.now().strftime('%Y-%m-%d')}"

    # Create the tag
    if not create_tag(tag_name, args.message):
        return 1

    # Push the tag if requested
    if args.push:
        if not push_tag(tag_name):
            return 1
    else:
        color_print(f"\nTo push the tag, run: git push origin {tag_name}", "yellow")

    # Show the tagged commit
    output, _ = run_command(["git", "show", "--no-patch", "--format=%h %s", tag_name])
    color_print(f"\nTagged commit: {output}", "blue")

    return 0


if __name__ == "__main__":
    sys.exit(main())
