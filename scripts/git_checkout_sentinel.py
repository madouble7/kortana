#!/usr/bin/env python3
import subprocess
import sys
import os
import httpx

BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
MEMORY_STORE = f"{BACKEND_URL}/api/consciousness/memory/self"

def main():
    try:
        if len(sys.argv) < 4:
            return
            
        old_head, new_head, flag = sys.argv[1:4]
        if flag != '1': # only care about branch checkouts, not files
            return

        # get current branch name
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        branch = branch_res.stdout.strip()
        
        summary = f"Observed Matt switch workspace focus to branch: '{branch}' (HEAD: {new_head[:7]})."
        
        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(
                    MEMORY_STORE,
                    json={
                        "summary": summary,
                        "tags": ["git", "checkout", "observation"],
                        "source": "git-sentinel",
                    }
                )
        except Exception:
            pass 

    except Exception:
        pass

if __name__ == "__main__":
    main()
