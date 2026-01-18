#!/usr/bin/env python3
"""
Daily autonomy sync - generates daily status log
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def get_git_stats():
    """Get current git stats"""
    try:
        # Count commits today
        today = datetime.now().strftime("%Y-%m-%d")
        commits = (
            subprocess.run(
                ["git", "log", "--since", f"{today} 00:00:00", "--oneline"],
                capture_output=True,
                text=True,
            )
            .stdout.strip()
            .split("\n")
            if subprocess.run(
                ["git", "log", "--since", f"{today} 00:00:00", "--oneline"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            else []
        )

        # Get current branch
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
        ).stdout.strip()

        # Count open PRs (if in workflow context)
        return {
            "commits_today": len(commits),
            "current_branch": current_branch,
            "has_uncommitted_changes": bool(
                subprocess.run(
                    ["git", "status", "--porcelain"], capture_output=True, text=True
                ).stdout.strip()
            ),
        }
    except Exception as e:
        return {"error": str(e)}


def check_backend_health():
    """Check if backend is healthy"""
    try:
        import requests

        response = requests.get("http://localhost:8000/api/health", timeout=2)
        return {"status": "alive" if response.status_code == 200 else "down"}
    except Exception:
        return {"status": "offline"}


def get_deployment_status():
    """Get last deployment info"""
    try:
        # Parse Cloud Run service info if available
        result = subprocess.run(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                "kortana-backend",
                "--region",
                "us-west1",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "last_deployment": data.get("metadata", {}).get("generation"),
                "url": data.get("status", {}).get("url", "N/A"),
            }
    except Exception:
        pass

    return {"status": "unavailable"}


def main():
    # Create logs/daily directory
    log_dir = Path("logs/daily")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.isoformat()

    # Gather data
    git_stats = get_git_stats()
    backend_health = check_backend_health()
    deployment = get_deployment_status()

    # Create log content
    log_content = f"""# Daily Autonomy Sync - {date_str}

**Timestamp**: {timestamp}

## Status

- **Backend**: {backend_health.get("status", "unknown")}
- **Current Branch**: {git_stats.get("current_branch", "unknown")}
- **Uncommitted Changes**: {"Yes" if git_stats.get("has_uncommitted_changes") else "No"}

## Activity

- **Commits Today**: {git_stats.get("commits_today", 0)}
- **Last Deployment**: {deployment.get("last_deployment", "N/A")}

## Metrics

```json
{
        json.dumps(
            {"git": git_stats, "backend": backend_health, "deployment": deployment},
            indent=2,
        )
    }
```

## Notes

Kor'tana is alive and monitoring.
"""

    # Write log file
    log_file = log_dir / f"{date_str}.md"
    log_file.write_text(log_content)

    print(f"✓ Daily sync log written: {log_file}")
    return 0


if __name__ == "__main__":
    exit(main())
