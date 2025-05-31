# relay_agent_output.py

import os


def read_last_message(log_path):
    if not os.path.exists(log_path):
        return None
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        return lines[-1].strip() if lines else None


def write_to_input_queue(message, input_path):
    if message:
        with open(input_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
        print(f"[relay] message relayed to {input_path}")
    else:
        print("[relay] no message found to relay.")


# example usage:
agent1_log = "logs/flash.log"
agent2_input = "queues/claude_in.txt"

latest = read_last_message(agent1_log)
write_to_input_queue(latest, agent2_input)
