#!/usr/bin/env python3
"""
CLI for Kor'tana's concurrent agent mesh.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_MESH_PATH = PROJECT_ROOT / "src" / "kortana" / "core" / "agent_mesh.py"

if not AGENT_MESH_PATH.exists():
    raise RuntimeError(f"Agent mesh module not found: {AGENT_MESH_PATH}")

_SPEC = importlib.util.spec_from_file_location("kortana_agent_mesh_runtime", AGENT_MESH_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load module spec from: {AGENT_MESH_PATH}")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ConcurrentAgentMesh = _MODULE.ConcurrentAgentMesh


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Concurrent multi-agent mesh CLI")
    parser.add_argument(
        "--state",
        default=str(PROJECT_ROOT / "state" / "agent_mesh_state.json"),
        help="Path to agent mesh state file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    register = sub.add_parser("register", help="Register or refresh an agent")
    register.add_argument("--agent", required=True)
    register.add_argument("--role", required=True)
    register.add_argument("--branch")
    register.add_argument("--capability", action="append", default=[])
    register.add_argument("--ttl", type=int, default=120)

    unregister = sub.add_parser("unregister", help="Unregister an agent")
    unregister.add_argument("--agent", required=True)
    unregister.add_argument("--reason", default="")

    heartbeat = sub.add_parser("heartbeat", help="Send heartbeat for an agent")
    heartbeat.add_argument("--agent", required=True)
    heartbeat.add_argument("--status")
    heartbeat.add_argument("--note")
    heartbeat.add_argument("--task-id")

    add_task = sub.add_parser("add-task", help="Add or update a task")
    add_task.add_argument("--task-id", required=True)
    add_task.add_argument("--title", required=True)
    add_task.add_argument("--description", required=True)
    add_task.add_argument("--priority", type=int, default=50)
    add_task.add_argument("--file", action="append", default=[])
    add_task.add_argument("--tag", action="append", default=[])
    add_task.add_argument("--created-by")

    claim_task = sub.add_parser("claim-task", help="Claim an existing task")
    claim_task.add_argument("--agent", required=True)
    claim_task.add_argument("--task-id", required=True)
    claim_task.add_argument("--ttl", type=int, default=120)

    release_task = sub.add_parser("release-task", help="Release a claimed task")
    release_task.add_argument("--agent", required=True)
    release_task.add_argument("--task-id", required=True)
    release_task.add_argument(
        "--outcome",
        default="completed",
        choices=["completed", "failed", "abandoned", "queued"],
    )
    release_task.add_argument("--note", default="")

    claim_files = sub.add_parser("claim-files", help="Claim file ownership")
    claim_files.add_argument("--agent", required=True)
    claim_files.add_argument("--file", action="append", required=True)
    claim_files.add_argument("--task-id")
    claim_files.add_argument("--ttl", type=int, default=120)
    claim_files.add_argument("--force", action="store_true")

    release_files = sub.add_parser("release-files", help="Release file ownership")
    release_files.add_argument("--agent", required=True)
    release_files.add_argument("--file", action="append", required=True)
    release_files.add_argument("--reason", default="")

    sub.add_parser("sweep", help="Remove stale agents/claims and requeue stale tasks")
    sub.add_parser("status", help="Show current coordination status")
    sub.add_parser("show", help="Show full raw state")

    recommend = sub.add_parser("recommend", help="Recommend next task for an agent")
    recommend.add_argument("--agent", required=True)

    assignments = sub.add_parser(
        "assignments",
        help="Suggest assignments across idle agents and queued tasks",
    )
    assignments.add_argument("--max", type=int, default=5)

    guide = sub.add_parser("guide", help="Show live guidance for one agent")
    guide.add_argument("--agent", required=True)

    return parser


def _print_human_status(status: dict) -> None:
    counts = status["counts"]
    print("Agent Mesh Status")
    print("-" * 72)
    print(
        "Agents: "
        f"{counts['agents_active']}/{counts['agents_total']} active, "
        f"{counts['agents_busy']} busy"
    )
    print(
        "Tasks: "
        f"{counts['queued']} queued, "
        f"{counts['in_progress']} in_progress, "
        f"{counts['completed']} completed, "
        f"{counts['failed']} failed, "
        f"{counts['abandoned']} abandoned"
    )
    print(f"Claims: {counts['claims_active']} active")
    print(f"Updated: {status['updated_at']}")

    if status["agents"]:
        print("\nAgents")
        for agent in status["agents"]:
            print(
                f"- {agent['agent_id']} role={agent.get('role')} "
                f"status={agent.get('status')} task={agent.get('current_task_id') or '-'}"
            )

    queued_tasks = [task for task in status["tasks"] if task.get("status") == "queued"]
    if queued_tasks:
        print("\nTop Queued Tasks")
        for task in queued_tasks[:10]:
            print(
                f"- {task['task_id']} priority={task.get('priority')} "
                f"title={task.get('title')}"
            )

    if status["claims"]:
        print("\nActive Claims")
        for claim in status["claims"][:15]:
            print(
                f"- {claim['file']} owner={claim.get('agent_id')} "
                f"task={claim.get('task_id') or '-'}"
            )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    mesh = ConcurrentAgentMesh(state_path=args.state)

    if args.command == "register":
        result = mesh.register_agent(
            agent_id=args.agent,
            role=args.role,
            branch=args.branch,
            capabilities=args.capability,
            ttl_seconds=args.ttl,
        )
    elif args.command == "unregister":
        result = mesh.unregister_agent(agent_id=args.agent, reason=args.reason)
    elif args.command == "heartbeat":
        result = mesh.heartbeat(
            agent_id=args.agent,
            status=args.status,
            note=args.note,
            current_task_id=args.task_id,
        )
    elif args.command == "add-task":
        result = mesh.add_task(
            task_id=args.task_id,
            title=args.title,
            description=args.description,
            priority=args.priority,
            files=args.file,
            tags=args.tag,
            created_by=args.created_by,
        )
    elif args.command == "claim-task":
        result = mesh.claim_task(
            agent_id=args.agent,
            task_id=args.task_id,
            ttl_seconds=args.ttl,
        )
    elif args.command == "release-task":
        result = mesh.release_task(
            agent_id=args.agent,
            task_id=args.task_id,
            outcome=args.outcome,
            note=args.note,
        )
    elif args.command == "claim-files":
        result = mesh.claim_files(
            agent_id=args.agent,
            files=args.file,
            task_id=args.task_id,
            ttl_seconds=args.ttl,
            force=args.force,
        )
    elif args.command == "release-files":
        result = mesh.release_files(
            agent_id=args.agent,
            files=args.file,
            reason=args.reason,
        )
    elif args.command == "sweep":
        result = mesh.sweep_stale()
    elif args.command == "status":
        status = mesh.status()
        if args.json:
            _print_json(status)
            return 0
        _print_human_status(status)
        return 0
    elif args.command == "show":
        result = mesh.export_state()
    elif args.command == "recommend":
        result = mesh.recommend_next_task(agent_id=args.agent)
    elif args.command == "assignments":
        result = mesh.suggest_assignments(max_items=args.max)
    elif args.command == "guide":
        result = {"agent_id": args.agent, "guidance": mesh.guidance(args.agent)}
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    if args.json:
        _print_json(result)
        return 0

    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")
    elif isinstance(result, list):
        if not result:
            print("(no entries)")
        for item in result:
            print(item)
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
