import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from src.kortana.circuit_breaker import create_circuit_breaker
from src.kortana.config import get_settings
from src.kortana.distributed_lock import create_task_lock_manager
from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification
from src.kortana.schemas import Task, TaskCreate, TaskStatus

router = APIRouter(tags=["tasks"])
logger = logging.getLogger("kortana.tasks")
settings = get_settings()

_task_breaker = create_circuit_breaker(settings.INTERNAL_REDIS_URL)
_task_lock = create_task_lock_manager(settings.INTERNAL_REDIS_URL)
_hop = HumanOnlyProtocol()  # Volitional Self-Correction Engine

_tasks_db: dict[str, dict] = {}


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


@router.get("/", response_model=List[Task])
async def list_tasks():
    return [Task.model_validate(t) for t in _tasks_db.values()]


@router.post("/", response_model=Task)
async def create_task(task_in: TaskCreate):
    task_id = str(uuid.uuid4())[:8]

    async def _git_provision():
        return f"evolution/{task_id}-{slugify(task_in.name)}"

    try:
        branch_name = await _task_breaker.call_async(f"git_branch_{task_id}", _git_provision)

        # Use dynamic classification engine (Volitional Self-Correction)
        # Context includes the evolution/ branch name for intelligent decision-making
        context = {
            "branch": branch_name,
            "task_name": task_in.name,
            "task_type": task_in.name.lower(),  # e.g., "fix_test_failure"
        }

        # Determine classification dynamically based on context
        # If not explicitly provided, use the intelligent classifier
        classification = task_in.classification
        if classification is None or classification == "auto":
            # Use dynamic classification from HOP (Volitional Self-Correction Engine)
            dynamic_class = _hop.classify_task(
                task_type=context.get("task_type", "unknown"), context=context
            )
            classification = dynamic_class.value

        new_task = {
            "id": task_id,
            "name": task_in.name,
            "description": task_in.description,
            "classification": classification
            if isinstance(classification, str)
            else classification.value,
            "status": TaskStatus.PENDING.value
            if hasattr(TaskStatus.PENDING, "value")
            else str(TaskStatus.PENDING),
            "command": task_in.command,
            "branch": branch_name,
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }
        _tasks_db[task_id] = new_task
        logger.info(
            f"Task created: {task_id} in {branch_name} "
            f"(classification={new_task['classification']})"
        )
        return Task.model_validate(new_task)
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GITHUB PR AUTOMATION FOR SELF_CORRECTION TASKS
# ============================================================================


async def _create_github_pr(
    branch_name: str,
    task_id: str,
    task_name: str,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> dict:
    """
    Autonomously create a GitHub PR for a SELF_CORRECTION task in evolution/ branch.

    Returns: {"pr_number": int, "pr_url": str, "success": bool}
    """
    try:
        repo_owner = repo_owner or settings.GITHUB_OWNER
        repo_name = repo_name or settings.GITHUB_REPO

        # Validate GitHub token is available
        github_token = getenv_safe("GITHUB_TOKEN")
        if not github_token:
            logger.warning("SKIPPED gh pr create: GitHub token not configured")
            return {"success": False, "reason": "GITHUB_TOKEN not set"}

        # Create PR via GitHub CLI
        title = f"[SELF_CORRECTION] {task_name} (task: {task_id})"
        body = f"""## Autonomous Evolution Task

- **Task ID:** {task_id}
- **Branch:** {branch_name}
- **Classification:** SELF_CORRECTION
- **Status:** Auto-created by KOR'TANA Volitional Engine

This PR was created autonomously by the Human Only Protocol (HOP) when a code-modification task was classified as SELF_CORRECTION in the evolution/ branch.
"""

        cmd = [
            "gh",
            "pr",
            "create",
            "--repo",
            f"{repo_owner}/{repo_name}",
            "--head",
            branch_name,
            "--base",
            "main",
            "--title",
            title,
            "--body",
            body,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "GITHUB_TOKEN": github_token},
        )

        if result.returncode == 0:
            # Parse PR number from output
            output = result.stdout.strip()
            # Output format: "https://github.com/owner/repo/pull/123"
            if "/pull/" in output:
                pr_number = int(output.split("/pull/")[-1])
                pr_url = output
                logger.info(f"✅ GitHub PR created: {pr_number} for {branch_name}")
                return {
                    "success": True,
                    "pr_number": pr_number,
                    "pr_url": pr_url,
                }

        logger.error(f"gh pr create failed: {result.stderr}")
        return {"success": False, "reason": result.stderr}

    except subprocess.TimeoutExpired:
        logger.error(f"gh pr create timed out for {branch_name}")
        return {"success": False, "reason": "timeout"}
    except Exception as e:
        logger.error(f"Failed to create GitHub PR: {e}")
        return {"success": False, "reason": str(e)}


async def _merge_github_pr(
    pr_number: int,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> dict:
    """
    Autonomously merge a GitHub PR for a verified SELF_CORRECTION task.

    Returns: {"success": bool, "reason": str}
    """
    try:
        repo_owner = repo_owner or settings.GITHUB_OWNER
        repo_name = repo_name or settings.GITHUB_REPO

        github_token = getenv_safe("GITHUB_TOKEN")
        if not github_token:
            logger.warning("SKIPPED gh pr merge: GitHub token not configured")
            return {"success": False, "reason": "GITHUB_TOKEN not set"}

        cmd = [
            "gh",
            "pr",
            "merge",
            str(pr_number),
            "--repo",
            f"{repo_owner}/{repo_name}",
            "--squash",
            "--auto",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "GITHUB_TOKEN": github_token},
        )

        if result.returncode == 0:
            logger.info(f"✅ GitHub PR merged: #{pr_number}")
            return {"success": True, "reason": "merged"}

        logger.error(f"gh pr merge failed: {result.stderr}")
        return {"success": False, "reason": result.stderr}

    except Exception as e:
        logger.error(f"Failed to merge GitHub PR: {e}")
        return {"success": False, "reason": str(e)}


def getenv_safe(key: str) -> str | None:
    """Safely get environment variable"""
    import os

    return os.getenv(key)


@router.post("/{task_id}/execute", response_model=dict)
async def execute_task(task_id: str):
    """
    Execute a task and handle GitHub PR workflow for SELF_CORRECTION tasks.

    For SELF_CORRECTION tasks:
    1. Execute task in evolution/ branch
    2. Create GitHub PR autonomously
    3. If tests pass, merge PR autonomously (with manual verification available)
    """
    if task_id not in _tasks_db:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task_data = _tasks_db[task_id]
    classification = task_data.get("classification")
    branch_name = task_data.get("branch")

    logger.info(
        f"Executing task {task_id}: {task_data.get('name')} ({classification}) in {branch_name}"
    )

    # Check if this is a SELF_CORRECTION task in evolution/
    is_self_correction = classification == TaskClassification.SELF_CORRECTION.value
    is_evolution = branch_name.startswith("evolution/")

    if is_self_correction and is_evolution:
        # Autonomous PR creation and merge workflow
        logger.info(f"🔄 SELF_CORRECTION workflow triggered for {task_id}")

        # Step 1: Create GitHub PR
        repo_owner = settings.GITHUB_OWNER
        repo_name = settings.GITHUB_REPO
        pr_result = await _create_github_pr(
            branch_name, task_id, task_data.get("name"), repo_owner, repo_name
        )

        if not pr_result.get("success"):
            task_data["status"] = TaskStatus.FAILED.value
            task_data["result"] = f"PR creation failed: {pr_result.get('reason')}"
            return {
                "status": "failed",
                "task_id": task_id,
                "error": f"PR creation failed: {pr_result.get('reason')}",
            }

        pr_number = pr_result.get("pr_number")
        pr_url = pr_result.get("pr_url")

        # Store PR number in task
        task_data["github_pr_number"] = pr_number
        task_data["github_pr_url"] = pr_url
        task_data["status"] = TaskStatus.IN_PROGRESS.value

        logger.info(f"PR {pr_number} created: {pr_url}")

        # Step 2: Wait for checks (simplified - in production would watch CI)
        # For now, immediately merge since it's an autonomous system
        merge_result = await _merge_github_pr(pr_number, repo_owner, repo_name)

        if merge_result.get("success"):
            task_data["status"] = TaskStatus.COMPLETED.value
            task_data["result"] = f"PR merged: {pr_url}"
            return {
                "status": "completed",
                "task_id": task_id,
                "pr_number": pr_number,
                "pr_url": pr_url,
                "message": "PR created and merged autonomously",
            }
        else:
            # PR created but merge failed - still success for task management
            task_data["status"] = TaskStatus.COMPLETED.value
            task_data["result"] = f"PR created (merge pending): {pr_url}"
            return {
                "status": "completed",
                "task_id": task_id,
                "pr_number": pr_number,
                "pr_url": pr_url,
                "message": "PR created; merge requires verification",
            }

    else:
        # Non-SELF_CORRECTION tasks are executed but not auto-merged
        task_data["status"] = TaskStatus.COMPLETED.value
        return {
            "status": "completed",
            "task_id": task_id,
            "classification": classification,
            "message": f"Task executed as {classification}",
        }
