# relay_agent_output.py

import os

try:
    from relays.protocol import append_text_line
except ModuleNotFoundError:
    from protocol import append_text_line


def read_last_message(log_path):
    if not os.path.exists(log_path):
        return None
    with open(log_path, encoding="utf-8") as f:
        content = f.read()
    if not content:
        return None

    lines = content.splitlines()
    # Skip incomplete trailing line to avoid relaying partial writes.
    if content and not content.endswith(("\n", "\r")):
        lines = lines[:-1]
    if not lines:
        return None
    return lines[-1].strip()


def write_to_input_queue(message, input_path):
    if message:
        append_text_line(input_path, message)
        print(f"[relay] message relayed to {input_path}")
    else:
        print("[relay] no message found to relay.")


# example usage:
agent1_log = "logs/flash.log"
agent2_input = "queues/claude_in.txt"

latest = read_last_message(agent1_log)
write_to_input_queue(latest, agent2_input)
