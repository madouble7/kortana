#!/usr/bin/env python3
import subprocess
import os
import httpx
import json
import traceback

BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
MEMORY_STORE = f"{BACKEND_URL}/api/consciousness/memory/self"

def main():
    try:
        # Get the latest commit hash, author, date, and message
        log_res = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h|%an|%ad|%s"],
            capture_output=True, text=True, check=True
        )
        parts = log_res.stdout.strip().split('|', 3)
        if len(parts) != 4:
            return
            
        commit_hash, author, date, message = parts
        
        # Get stat of files changed
        stat_res = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", commit_hash],
            capture_output=True, text=True
        )
        files_changed = []
        for line in stat_res.stdout.strip().splitlines():
            if line:
                parts = line.split('\t')
                files_changed.append(f"{parts[0]} {parts[-1]}")
        
        summary = (
            f"Observed commit {commit_hash} by {author}: '{message}'.\n"
            f"Files altered:\n" + '\n'.join(files_changed)
        )
        
        # We don't want to block the commit
        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(
                    MEMORY_STORE,
                    json={
                        "summary": summary,
                        "tags": ["git", "commit", "observation"],
                        "source": "git-sentinel",
                    }
                )
        except Exception:
            pass # Failing silently is preferred to disrupting Matt's git workflow

    except Exception:
        pass

if __name__ == "__main__":
    main()
