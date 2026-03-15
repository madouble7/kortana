import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from kortana.agent_manager import AgentManager

if __name__ == "__main__":
    _, mode, *args = sys.argv
    mgr = AgentManager()
    if mode == "ingest":
        text = open(args[0], encoding="utf-8").read()
        results = mgr.run(
            "memory", text=text, verify_query=args[1] if len(args) > 1 else ""
        )
        print("Top matches:", results)
    else:
        print("Usage: python run_memory_agent.py ingest <path> [verify_query]")
