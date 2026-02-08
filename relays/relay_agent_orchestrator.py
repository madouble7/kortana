#!/usr/bin/env python3
"""
Kor'tana Relay Agent Orchestrator
================================

Minimal autonomous relay system:
- Scans all /logs/*.log files
- Relays new lines to matching /queues/*_in.txt
- Tracks what's been relayed (no duplicates)
- Loops every 2 seconds

Usage:
    cd relays
    python relay_agent_orchestrator.py
"""

import json
import os
import time

try:
    from relays.protocol import append_text_line, tail_text_lines
except ModuleNotFoundError:
    from protocol import append_text_line, tail_text_lines

LOGS_DIR = "../logs"
QUEUES_DIR = "../queues"
SEEN_DIR = "../relays/.seen"

os.makedirs(SEEN_DIR, exist_ok=True)
os.makedirs(QUEUES_DIR, exist_ok=True)


def get_seen_path(log_file):
    """Get the path to the .seen file for tracking processed lines"""
    base = os.path.basename(log_file)
    return os.path.join(SEEN_DIR, base + ".seen")


def _load_seen_state(seen_path):
    """Load seen state using byte offset + partial-line remainder."""
    default = {"offset": 0, "remainder": ""}
    if not os.path.exists(seen_path):
        return default

    try:
        with open(seen_path, encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return default

        # New format: JSON
        if raw.startswith("{"):
            data = json.loads(raw)
            if isinstance(data, dict):
                return {
                    "offset": int(data.get("offset", 0) or 0),
                    "remainder": str(data.get("remainder", "") or ""),
                }

        # Legacy format: line count
        legacy_count = int(raw)
        return {"offset": 0, "remainder": "", "legacy_line_count": legacy_count}
    except Exception:
        return default


def _save_seen_state(seen_path, state):
    """Persist seen state atomically."""
    tmp_path = seen_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "offset": int(state.get("offset", 0) or 0),
                "remainder": str(state.get("remainder", "") or ""),
            },
            f,
            indent=2,
        )
        f.write("\n")
    os.replace(tmp_path, seen_path)


def read_new_lines(log_file):
    """Read only new complete lines since last processing."""
    seen_path = get_seen_path(log_file)
    seen_state = _load_seen_state(seen_path)

    # Check if log file exists
    if not os.path.exists(log_file):
        return [], seen_state

    last_offset = int(seen_state.get("offset", 0) or 0)
    remainder = str(seen_state.get("remainder", "") or "")

    # One-time migration for legacy line-count state.
    legacy_line_count = seen_state.get("legacy_line_count")
    if legacy_line_count is not None:
        try:
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()
            capped = max(0, min(int(legacy_line_count), len(lines)))
            last_offset = len("".join(lines[:capped]).encode("utf-8"))
        except Exception:
            last_offset = 0

    lines, next_offset, next_remainder = tail_text_lines(
        log_file,
        offset=last_offset,
        remainder=remainder,
    )
    new_lines = [line for line in lines if line.strip()]
    return new_lines, {"offset": next_offset, "remainder": next_remainder}


def write_to_queue(agent, lines):
    """Write new messages to agent's input queue"""
    if not lines:
        return

    queue_file = os.path.join(QUEUES_DIR, f"{agent}_in.txt")

    for line in lines:
        append_text_line(queue_file, line.rstrip("\n"))

    print(f"[relay] relayed {len(lines)} message(s) to {queue_file}")


def relay_all():
    """Process all log files and relay new messages"""
    for log_file in os.listdir(LOGS_DIR):
        if not log_file.endswith(".log"):
            continue

        agent = log_file.replace(".log", "")
        full_log_path = os.path.join(LOGS_DIR, log_file)

        # Get new lines since last check
        new_lines, next_state = read_new_lines(full_log_path)

        # Relay to queue if there are new messages
        if new_lines:
            write_to_queue(agent, new_lines)

        # Update seen file with current byte offset + remainder state.
        seen_path = get_seen_path(full_log_path)
        _save_seen_state(seen_path, next_state)


if __name__ == "__main__":
    print("🔄 kor'tana relay orchestrator started...")
    print(f"📁 Watching: {LOGS_DIR}")
    print(f"📤 Relaying to: {QUEUES_DIR}")
    print("💡 Press Ctrl+C to stop")
    print()

    try:
        while True:
            relay_all()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Relay orchestrator stopped")
