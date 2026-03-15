"""
Concurrent agent mesh for real-time multi-agent coordination.

This module provides a filesystem-backed coordination model so multiple agents can:
- register and heartbeat
- create and claim tasks
- claim files before editing
- release claims and complete work
- detect stale ownership and recover automatically
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class ConcurrentAgentMesh:
    """Filesystem-backed coordination state for concurrent autonomous agents."""

    def __init__(
        self,
        state_path: str | Path | None = None,
        lock_timeout_seconds: float = 10.0,
    ) -> None:
        self.project_root = self._detect_project_root()
        self.state_path = (
            Path(state_path).resolve()
            if state_path is not None
            else self.project_root / "state" / "agent_mesh_state.json"
        )
        self.events_path = self.state_path.with_suffix(".events.jsonl")
        self.lock_path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        self.lock_timeout_seconds = lock_timeout_seconds

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_state_file()

    def _detect_project_root(self) -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                return parent
        return Path.cwd().resolve()

    def _empty_state(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "updated_at": _utc_now_iso(),
            "agents": {},
            "tasks": {},
            "claims": {},
        }

    def _ensure_state_file(self) -> None:
        if self.state_path.exists():
            return
        self._write_state_unlocked(self._empty_state())

    def _read_state_unlocked(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._empty_state()
        with open(self.state_path, encoding="utf-8") as handle:
            raw = json.load(handle)
        return self._ensure_shape(raw)

    def _ensure_shape(self, state: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(state, dict):
            return self._empty_state()
        state.setdefault("schema_version", 1)
        state.setdefault("updated_at", _utc_now_iso())
        state.setdefault("agents", {})
        state.setdefault("tasks", {})
        state.setdefault("claims", {})
        return state

    def _write_state_unlocked(self, state: dict[str, Any]) -> None:
        temp_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, self.state_path)

    def _record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "timestamp": _utc_now_iso(),
            "event_type": event_type,
            "payload": payload,
        }
        with open(self.events_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    def _acquire_lock(self) -> int:
        deadline = time.time() + self.lock_timeout_seconds
        while True:
            try:
                fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.write(fd, f"{os.getpid()} {_utc_now_iso()}".encode("utf-8"))
                return fd
            except FileExistsError:
                self._break_stale_lock()
                if time.time() >= deadline:
                    raise TimeoutError(
                        f"Timed out waiting for lock: {self.lock_path}"
                    ) from None
                time.sleep(0.05)

    def _break_stale_lock(self) -> None:
        if not self.lock_path.exists():
            return
        age = time.time() - self.lock_path.stat().st_mtime
        if age > max(30.0, self.lock_timeout_seconds * 3):
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                return

    def _release_lock(self, fd: int) -> None:
        try:
            os.close(fd)
        finally:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass

    def _mutate_state(self, mutator) -> Any:
        lock_fd = self._acquire_lock()
        try:
            state = self._read_state_unlocked()
            result = mutator(state)
            state["updated_at"] = _utc_now_iso()
            self._write_state_unlocked(state)
            return result
        finally:
            self._release_lock(lock_fd)

    def _read_state_snapshot(self) -> dict[str, Any]:
        return self._read_state_unlocked()

    def _normalize_file(self, file_path: str) -> str:
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = (self.project_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            return candidate.relative_to(self.project_root).as_posix()
        except ValueError:
            return candidate.as_posix()

    def _claim_is_stale(
        self,
        claim: dict[str, Any],
        agents: dict[str, Any],
        now: datetime,
    ) -> bool:
        claim_ts = _parse_iso(claim.get("heartbeat_at") or claim.get("claimed_at"))
        if claim_ts is None:
            return True
        ttl_seconds = int(claim.get("ttl_seconds", 120))
        if (now - claim_ts).total_seconds() > ttl_seconds:
            return True
        owner = agents.get(claim.get("agent_id", ""))
        if owner is None:
            return True
        owner_ts = _parse_iso(owner.get("last_heartbeat"))
        owner_ttl = int(owner.get("ttl_seconds", 120))
        if owner_ts is None:
            return True
        if (now - owner_ts).total_seconds() > owner_ttl:
            return True
        return False

    def _agent_is_stale(self, agent: dict[str, Any], now: datetime) -> bool:
        heartbeat = _parse_iso(agent.get("last_heartbeat"))
        if heartbeat is None:
            return True
        ttl_seconds = int(agent.get("ttl_seconds", 120))
        return (now - heartbeat).total_seconds() > ttl_seconds

    def _sweep_stale_inplace(self, state: dict[str, Any]) -> dict[str, int]:
        now = datetime.now(UTC)
        agents = state["agents"]
        claims = state["claims"]
        tasks = state["tasks"]

        stale_agents = [
            agent_id
            for agent_id, agent in agents.items()
            if self._agent_is_stale(agent, now)
        ]
        for agent_id in stale_agents:
            agents.pop(agent_id, None)

        stale_claims = []
        for normalized_path, claim in claims.items():
            if self._claim_is_stale(claim, agents, now):
                stale_claims.append(normalized_path)
        for normalized_path in stale_claims:
            claims.pop(normalized_path, None)

        requeued_tasks = 0
        live_agents = set(agents.keys())
        for task in tasks.values():
            assigned = task.get("assigned_agent")
            if task.get("status") == "in_progress" and assigned not in live_agents:
                task["status"] = "queued"
                task["assigned_agent"] = None
                task["claimed_at"] = None
                requeued_tasks += 1

        return {
            "stale_agents_removed": len(stale_agents),
            "stale_claims_removed": len(stale_claims),
            "requeued_tasks": requeued_tasks,
        }

    def register_agent(
        self,
        agent_id: str,
        role: str,
        branch: str | None = None,
        capabilities: list[str] | None = None,
        ttl_seconds: int = 120,
    ) -> dict[str, Any]:
        now = _utc_now_iso()
        capabilities = capabilities or []

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            self._sweep_stale_inplace(state)
            existing = state["agents"].get(agent_id)
            state["agents"][agent_id] = {
                "agent_id": agent_id,
                "role": role,
                "branch": branch,
                "capabilities": capabilities,
                "status": "idle",
                "current_task_id": existing.get("current_task_id") if existing else None,
                "note": existing.get("note") if existing else "",
                "registered_at": existing.get("registered_at", now) if existing else now,
                "last_heartbeat": now,
                "ttl_seconds": ttl_seconds,
            }
            return {"created": existing is None, "agent": state["agents"][agent_id]}

        result = self._mutate_state(mutate)
        self._record_event("agent.register", {"agent_id": agent_id, "role": role})
        return result

    def unregister_agent(self, agent_id: str, reason: str = "") -> dict[str, Any]:
        now = _utc_now_iso()

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            agent = state["agents"].pop(agent_id, None)
            if agent is None:
                return {"removed": False, "reason": "agent_not_found"}

            for normalized_path in list(state["claims"].keys()):
                claim = state["claims"][normalized_path]
                if claim.get("agent_id") == agent_id:
                    state["claims"].pop(normalized_path, None)

            for task in state["tasks"].values():
                if task.get("assigned_agent") == agent_id and task.get("status") == "in_progress":
                    task["status"] = "queued"
                    task["assigned_agent"] = None
                    task["claimed_at"] = None
                    task["updated_at"] = now

            return {"removed": True, "agent": agent}

        result = self._mutate_state(mutate)
        if result.get("removed"):
            self._record_event(
                "agent.unregister",
                {"agent_id": agent_id, "reason": reason},
            )
        return result

    def heartbeat(
        self,
        agent_id: str,
        status: str | None = None,
        note: str | None = None,
        current_task_id: str | None = None,
    ) -> dict[str, Any]:
        now = _utc_now_iso()

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            self._sweep_stale_inplace(state)
            agent = state["agents"].get(agent_id)
            if agent is None:
                agent = {
                    "agent_id": agent_id,
                    "role": "unknown",
                    "branch": None,
                    "capabilities": [],
                    "status": "idle",
                    "current_task_id": None,
                    "note": "",
                    "registered_at": now,
                    "last_heartbeat": now,
                    "ttl_seconds": 120,
                }
                state["agents"][agent_id] = agent
            agent["last_heartbeat"] = now
            if status is not None:
                agent["status"] = status
            if note is not None:
                agent["note"] = note
            if current_task_id is not None:
                agent["current_task_id"] = current_task_id

            for claim in state["claims"].values():
                if claim.get("agent_id") == agent_id:
                    claim["heartbeat_at"] = now

            return {"agent": agent}

        result = self._mutate_state(mutate)
        self._record_event(
            "agent.heartbeat",
            {"agent_id": agent_id, "status": status, "task_id": current_task_id},
        )
        return result

    def add_task(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: int = 50,
        files: list[str] | None = None,
        tags: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        files = files or []
        tags = tags or []
        normalized_files = sorted({self._normalize_file(path) for path in files})
        now = _utc_now_iso()

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            existing = state["tasks"].get(task_id)
            state["tasks"][task_id] = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
                "status": existing.get("status", "queued") if existing else "queued",
                "files": normalized_files,
                "tags": tags,
                "created_by": created_by,
                "created_at": existing.get("created_at", now) if existing else now,
                "updated_at": now,
                "assigned_agent": existing.get("assigned_agent") if existing else None,
                "claimed_at": existing.get("claimed_at") if existing else None,
                "completed_at": existing.get("completed_at") if existing else None,
                "outcome": existing.get("outcome") if existing else None,
                "note": existing.get("note") if existing else None,
            }
            return {"created": existing is None, "task": state["tasks"][task_id]}

        result = self._mutate_state(mutate)
        self._record_event("task.add", {"task_id": task_id, "priority": priority})
        return result

    def _claim_files_inplace(
        self,
        state: dict[str, Any],
        agent_id: str,
        files: list[str],
        task_id: str | None,
        ttl_seconds: int,
        force: bool,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        normalized_files = sorted({self._normalize_file(path) for path in files})
        conflicts: list[dict[str, Any]] = []
        claimed: list[str] = []

        for normalized_path in normalized_files:
            existing = state["claims"].get(normalized_path)
            if existing is not None:
                if self._claim_is_stale(existing, state["agents"], now):
                    state["claims"].pop(normalized_path, None)
                    existing = None

            if existing is not None and existing.get("agent_id") != agent_id and not force:
                conflicts.append(
                    {
                        "file": normalized_path,
                        "claimed_by": existing.get("agent_id"),
                        "task_id": existing.get("task_id"),
                    }
                )
                continue

            state["claims"][normalized_path] = {
                "file": normalized_path,
                "agent_id": agent_id,
                "task_id": task_id,
                "claimed_at": _utc_now_iso(),
                "heartbeat_at": _utc_now_iso(),
                "ttl_seconds": ttl_seconds,
            }
            claimed.append(normalized_path)

        return {"claimed": claimed, "conflicts": conflicts}

    def claim_files(
        self,
        agent_id: str,
        files: list[str],
        task_id: str | None = None,
        ttl_seconds: int = 120,
        force: bool = False,
    ) -> dict[str, Any]:
        files = files or []

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            self._sweep_stale_inplace(state)
            agent = state["agents"].get(agent_id)
            if agent is None:
                return {"success": False, "error": "agent_not_registered"}

            claim_result = self._claim_files_inplace(
                state=state,
                agent_id=agent_id,
                files=files,
                task_id=task_id,
                ttl_seconds=ttl_seconds,
                force=force,
            )
            success = len(claim_result["conflicts"]) == 0
            if success and claim_result["claimed"]:
                agent["status"] = "busy"
                agent["last_heartbeat"] = _utc_now_iso()
            return {"success": success, **claim_result}

        result = self._mutate_state(mutate)
        self._record_event(
            "claim.files",
            {
                "agent_id": agent_id,
                "task_id": task_id,
                "claimed_count": len(result.get("claimed", [])),
                "conflicts_count": len(result.get("conflicts", [])),
            },
        )
        return result

    def release_files(
        self,
        agent_id: str,
        files: list[str],
        reason: str = "",
    ) -> dict[str, Any]:
        normalized_targets = {self._normalize_file(path) for path in (files or [])}

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            released: list[str] = []
            for normalized_path in normalized_targets:
                claim = state["claims"].get(normalized_path)
                if claim and claim.get("agent_id") == agent_id:
                    state["claims"].pop(normalized_path, None)
                    released.append(normalized_path)
            return {"released": released}

        result = self._mutate_state(mutate)
        self._record_event(
            "claim.release_files",
            {"agent_id": agent_id, "released_count": len(result["released"]), "reason": reason},
        )
        return result

    def claim_task(
        self,
        agent_id: str,
        task_id: str,
        ttl_seconds: int = 120,
    ) -> dict[str, Any]:
        now = _utc_now_iso()

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            self._sweep_stale_inplace(state)
            agent = state["agents"].get(agent_id)
            if agent is None:
                return {"success": False, "error": "agent_not_registered"}

            task = state["tasks"].get(task_id)
            if task is None:
                return {"success": False, "error": "task_not_found"}

            if task.get("status") in {"completed", "failed", "abandoned"}:
                return {"success": False, "error": "task_already_closed"}

            assigned = task.get("assigned_agent")
            if assigned and assigned != agent_id:
                return {
                    "success": False,
                    "error": "task_assigned_to_other_agent",
                    "assigned_agent": assigned,
                }

            claim_result = self._claim_files_inplace(
                state=state,
                agent_id=agent_id,
                files=task.get("files", []),
                task_id=task_id,
                ttl_seconds=ttl_seconds,
                force=False,
            )
            if claim_result["conflicts"]:
                return {"success": False, "error": "file_conflicts", **claim_result}

            task["status"] = "in_progress"
            task["assigned_agent"] = agent_id
            task["claimed_at"] = now
            task["updated_at"] = now
            agent["current_task_id"] = task_id
            agent["status"] = "busy"
            agent["last_heartbeat"] = now
            return {"success": True, "task": task, **claim_result}

        result = self._mutate_state(mutate)
        self._record_event(
            "task.claim",
            {"agent_id": agent_id, "task_id": task_id, "success": result.get("success", False)},
        )
        return result

    def release_task(
        self,
        agent_id: str,
        task_id: str,
        outcome: str = "completed",
        note: str = "",
    ) -> dict[str, Any]:
        now = _utc_now_iso()
        normalized_outcome = outcome.lower()
        status_map = {
            "completed": "completed",
            "failed": "failed",
            "abandoned": "abandoned",
            "queued": "queued",
        }
        target_status = status_map.get(normalized_outcome, "completed")

        def mutate(state: dict[str, Any]) -> dict[str, Any]:
            task = state["tasks"].get(task_id)
            if task is None:
                return {"success": False, "error": "task_not_found"}
            if task.get("assigned_agent") not in {agent_id, None} and task.get("status") == "in_progress":
                return {
                    "success": False,
                    "error": "task_owned_by_other_agent",
                    "assigned_agent": task.get("assigned_agent"),
                }

            task["status"] = target_status
            task["updated_at"] = now
            task["note"] = note or task.get("note")
            task["outcome"] = normalized_outcome
            if target_status in {"completed", "failed", "abandoned"}:
                task["completed_at"] = now
            task["assigned_agent"] = None

            released_files = []
            for normalized_path in list(state["claims"].keys()):
                claim = state["claims"][normalized_path]
                if claim.get("task_id") == task_id and claim.get("agent_id") == agent_id:
                    state["claims"].pop(normalized_path, None)
                    released_files.append(normalized_path)

            agent = state["agents"].get(agent_id)
            if agent is not None and agent.get("current_task_id") == task_id:
                agent["current_task_id"] = None
                if target_status == "queued":
                    agent["status"] = "busy"
                else:
                    agent["status"] = "idle"
                agent["last_heartbeat"] = now

            return {
                "success": True,
                "task": task,
                "released_files": released_files,
            }

        result = self._mutate_state(mutate)
        self._record_event(
            "task.release",
            {
                "agent_id": agent_id,
                "task_id": task_id,
                "outcome": normalized_outcome,
                "success": result.get("success", False),
            },
        )
        return result

    def sweep_stale(self) -> dict[str, int]:
        result = self._mutate_state(self._sweep_stale_inplace)
        self._record_event("mesh.sweep", result)
        return result

    def _task_blocked(self, task: dict[str, Any], claims: dict[str, Any], agent_id: str | None = None) -> bool:
        task_files = task.get("files", [])
        for normalized_path in task_files:
            claim = claims.get(normalized_path)
            if claim is None:
                continue
            owner = claim.get("agent_id")
            if owner and owner != agent_id:
                return True
        return False

    def recommend_next_task(self, agent_id: str) -> dict[str, Any]:
        snapshot = self._read_state_snapshot()
        agents = snapshot["agents"]
        tasks = snapshot["tasks"]
        claims = snapshot["claims"]

        agent = agents.get(agent_id)
        if agent is None:
            return {"success": False, "error": "agent_not_registered"}

        queued = [
            task
            for task in tasks.values()
            if task.get("status") == "queued"
            and not self._task_blocked(task, claims, agent_id=agent_id)
        ]
        queued.sort(key=lambda task: int(task.get("priority", 0)), reverse=True)

        if not queued:
            return {"success": True, "task": None}

        return {"success": True, "task": queued[0]}

    def suggest_assignments(self, max_items: int = 5) -> list[dict[str, Any]]:
        snapshot = self._read_state_snapshot()
        agents = snapshot["agents"]
        tasks = snapshot["tasks"]
        claims = snapshot["claims"]

        idle_agents = [
            agent
            for agent in agents.values()
            if agent.get("status") in {"idle", "blocked"}
        ]
        if not idle_agents:
            return []

        queued_tasks = [
            task
            for task in tasks.values()
            if task.get("status") == "queued" and not self._task_blocked(task, claims)
        ]
        queued_tasks.sort(key=lambda task: int(task.get("priority", 0)), reverse=True)

        suggestions: list[dict[str, Any]] = []
        for task in queued_tasks:
            best_score = None
            best_agent = None
            for agent in idle_agents:
                capabilities = set(agent.get("capabilities", []))
                tags = set(task.get("tags", []))
                capability_score = len(capabilities.intersection(tags))
                load_penalty = 1 if agent.get("current_task_id") else 0
                score = (capability_score * 2) - load_penalty
                if best_score is None or score > best_score:
                    best_score = score
                    best_agent = agent
            if best_agent is None:
                continue
            suggestions.append(
                {
                    "task_id": task.get("task_id"),
                    "task_title": task.get("title"),
                    "priority": task.get("priority"),
                    "suggested_agent_id": best_agent.get("agent_id"),
                    "score": best_score,
                }
            )
            if len(suggestions) >= max_items:
                break

        return suggestions

    def status(self) -> dict[str, Any]:
        snapshot = self._read_state_snapshot()
        agents = snapshot["agents"]
        tasks = snapshot["tasks"]
        claims = snapshot["claims"]

        task_counts = {
            "queued": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "abandoned": 0,
            "other": 0,
        }
        for task in tasks.values():
            status = str(task.get("status", "other"))
            if status in task_counts:
                task_counts[status] += 1
            else:
                task_counts["other"] += 1

        active_agents = sum(1 for agent in agents.values() if agent.get("status") != "offline")
        busy_agents = sum(1 for agent in agents.values() if agent.get("status") == "busy")

        return {
            "updated_at": snapshot.get("updated_at"),
            "counts": {
                "agents_total": len(agents),
                "agents_active": active_agents,
                "agents_busy": busy_agents,
                "claims_active": len(claims),
                **task_counts,
            },
            "agents": sorted(agents.values(), key=lambda item: item.get("agent_id", "")),
            "tasks": sorted(
                tasks.values(),
                key=lambda item: (
                    -int(item.get("priority", 0)),
                    item.get("task_id", ""),
                ),
            ),
            "claims": sorted(
                claims.values(),
                key=lambda item: item.get("file", ""),
            ),
        }

    def guidance(self, agent_id: str) -> list[str]:
        snapshot = self._read_state_snapshot()
        agents = snapshot["agents"]
        tasks = snapshot["tasks"]
        claims = snapshot["claims"]
        agent = agents.get(agent_id)

        guidance: list[str] = []
        if agent is None:
            guidance.append(
                f"Agent '{agent_id}' is not registered. Register first with: "
                f"python scripts/agent_mesh.py register --agent {agent_id} --role coding"
            )
            return guidance

        current_task_id = agent.get("current_task_id")
        if current_task_id:
            guidance.append(
                f"Continue task '{current_task_id}' and heartbeat every 30-60s."
            )
            owned_files = [
                claim["file"]
                for claim in claims.values()
                if claim.get("agent_id") == agent_id and claim.get("task_id") == current_task_id
            ]
            if owned_files:
                guidance.append(
                    "You currently own files: " + ", ".join(sorted(owned_files))
                )
        else:
            recommendation = self.recommend_next_task(agent_id)
            task = recommendation.get("task")
            if task:
                task_id = task.get("task_id")
                guidance.append(
                    f"Recommended next task: {task_id} (priority {task.get('priority')})."
                )
                guidance.append(
                    "Claim it with: "
                    f"python scripts/agent_mesh.py claim-task --agent {agent_id} --task-id {task_id}"
                )
            else:
                guidance.append(
                    "No unblocked queued tasks available. Add one or wait for new work."
                )

        blocked_count = 0
        for task in tasks.values():
            if task.get("status") == "queued" and self._task_blocked(task, claims):
                blocked_count += 1
        if blocked_count:
            guidance.append(
                f"{blocked_count} queued task(s) are blocked by file ownership. "
                "Run a sweep if ownership is stale: python scripts/agent_mesh.py sweep"
            )

        return guidance

    def export_state(self) -> dict[str, Any]:
        return self._read_state_snapshot()
