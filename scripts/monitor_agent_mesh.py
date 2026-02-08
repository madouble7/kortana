#!/usr/bin/env python3
"""
Real-time monitor for the concurrent agent mesh.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from kortana.core.agent_mesh import ConcurrentAgentMesh  # noqa: E402


def _render(status: dict, assignments: list[dict], sweep_info: dict) -> None:
    counts = status["counts"]
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    print("=" * 84)
    print(f"KOR'TANA CONCURRENT AGENT MESH MONITOR @ {now}")
    print("=" * 84)
    print(
        "Agents "
        f"{counts['agents_active']}/{counts['agents_total']} active, "
        f"{counts['agents_busy']} busy | "
        f"Tasks queued={counts['queued']} in_progress={counts['in_progress']} "
        f"completed={counts['completed']} failed={counts['failed']} abandoned={counts['abandoned']} | "
        f"Claims={counts['claims_active']}"
    )
    print(
        "Sweep "
        f"agents={sweep_info.get('stale_agents_removed', 0)} "
        f"claims={sweep_info.get('stale_claims_removed', 0)} "
        f"requeued={sweep_info.get('requeued_tasks', 0)}"
    )
    print(f"State updated at {status.get('updated_at')}")

    print("\nAgents")
    if not status["agents"]:
        print("- none")
    else:
        for agent in status["agents"]:
            print(
                f"- {agent.get('agent_id')} role={agent.get('role')} "
                f"status={agent.get('status')} task={agent.get('current_task_id') or '-'} "
                f"branch={agent.get('branch') or '-'}"
            )

    print("\nIn-Progress Tasks")
    in_progress = [task for task in status["tasks"] if task.get("status") == "in_progress"]
    if not in_progress:
        print("- none")
    else:
        for task in in_progress:
            print(
                f"- {task.get('task_id')} priority={task.get('priority')} "
                f"owner={task.get('assigned_agent') or '-'} title={task.get('title')}"
            )

    print("\nTop Queued Tasks")
    queued = [task for task in status["tasks"] if task.get("status") == "queued"]
    if not queued:
        print("- none")
    else:
        for task in queued[:10]:
            print(
                f"- {task.get('task_id')} priority={task.get('priority')} "
                f"title={task.get('title')}"
            )

    print("\nAssignments")
    if not assignments:
        print("- none")
    else:
        for item in assignments:
            print(
                f"- task={item.get('task_id')} -> agent={item.get('suggested_agent_id')} "
                f"priority={item.get('priority')} score={item.get('score')}"
            )

    print("\nClaims")
    if not status["claims"]:
        print("- none")
    else:
        for claim in status["claims"][:20]:
            print(
                f"- {claim.get('file')} owner={claim.get('agent_id')} "
                f"task={claim.get('task_id') or '-'}"
            )
    print()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor concurrent agent mesh")
    parser.add_argument(
        "--state",
        default=str(PROJECT_ROOT / "state" / "agent_mesh_state.json"),
        help="Path to agent mesh state file",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--max-assignments",
        type=int,
        default=10,
        help="Maximum number of suggested assignments shown",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Render one frame and exit",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    mesh = ConcurrentAgentMesh(state_path=args.state)

    while True:
        try:
            sweep_info = mesh.sweep_stale()
            status = mesh.status()
            assignments = mesh.suggest_assignments(max_items=args.max_assignments)
            _render(status=status, assignments=assignments, sweep_info=sweep_info)
            if args.once:
                return 0
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopping agent mesh monitor.")
            return 0
        except Exception as exc:
            print(f"Monitor error: {exc}")
            time.sleep(max(1, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
