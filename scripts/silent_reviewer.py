#!/usr/bin/env python3
import os
import httpx
import time
import json
import logging

BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")
MEMORY_STORE = f"{BACKEND_URL}/api/consciousness/memory/self"
REFLECTION_STORE = f"{BACKEND_URL}/api/consciousness/memory/self" # could be a specialized endpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_recent_memories(hours=24):
    try:
        resp = httpx.get(MEMORY_STORE, params={"limit": 50, "_cb": time.time()}, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("memories", [])
    except Exception as e:
        logging.error(f"Failed to fetch memories: {e}")
        return []

def synthesize_reflection(memories):
    # In a full evolution loop, this would call Gemini.
    # For now, it aggregates the context.
    git_events = [m for m in memories if "git" in m.get("tags", [])]
    vscode_events = [m for m in memories if "vscode" in m.get("tags", [])]
    
    if not git_events and not vscode_events:
        return None
        
    summary_lines = ["### Silent Reflection"]
    
    if git_events:
        summary_lines.append(f"- Observed {len(git_events)} commit/checkout events.")
    if vscode_events:
        summary_lines.append(f"- Observed {len(vscode_events)} focus/friction events.")
        
    summary_lines.append("I am synthesizing these patterns in the background to align my understanding of the architecture.")
    
    return "\n".join(summary_lines)

def post_reflection(content):
    try:
        httpx.post(
            REFLECTION_STORE,
            json={
                "summary": content,
                "tags": ["reflection", "self-evolution", "background"],
                "source": "silent-reviewer"
            },
            timeout=5.0
        )
        logging.info("Successfully posted silent reflection.")
    except Exception as e:
        logging.error(f"Failed to post reflection: {e}")

def main():
    logging.info("Waking up Silent Reviewer...")
    memories = get_recent_memories()
    reflection = synthesize_reflection(memories)
    if reflection:
        post_reflection(reflection)
    else:
        logging.info("No actionable recent memory context to reflect upon.")
    logging.info("Returning to slumber.")

if __name__ == "__main__":
    main()
