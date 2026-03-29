import asyncio
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import IncidentMemory

logger = logging.getLogger(__name__)


class VectorAlphaBranchService:
    """
    Handles branch-scoped self-healing for KOR'TANA via Vector Alpha constraints.
    - Never mutates the main worktree.
    - Creates auto-fix/<incident-type>-<timestamp> branches using an isolated git worktree.
    - Runs ruff and pytest locally inside the worktree before pushing or creating PR.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../../")
        )
        self.worktree_dir = os.path.join(self.repo_dir, ".vector_alpha_worktree")

    def evaluate_incident(self, incident: IncidentMemory) -> bool:
        if incident.resolved:
            return False

        allowed_types = ["daemon_crash", "task_failure", "broken_test", "test_failure"]
        if incident.incident_type not in allowed_types:
            return False

        if not incident.description:
            return False

        sensitive_keywords = ["auth", "billing", "secret", "deploy", "config", "token"]
        desc_lower = incident.description.lower()
        if any(sk in desc_lower for sk in sensitive_keywords):
            return False

        return True

    async def create_healing_branch(self, incident: IncidentMemory) -> Optional[str]:
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            sanitized_type = incident.incident_type.replace("_", "-")
            branch_name = f"auto-fix/{sanitized_type}-{timestamp}"

            if os.path.exists(self.worktree_dir):
                await asyncio.to_thread(
                    subprocess.run,
                    ["git", "worktree", "remove", "--force", self.worktree_dir],
                    cwd=self.repo_dir,
                    capture_output=True,
                    check=False,
                )

            res = await asyncio.to_thread(
                subprocess.run,
                ["git", "worktree", "add", "-B", branch_name, self.worktree_dir, "main"],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )
            if res.returncode != 0:
                logger.error(f"Failed to create worktree for branch: {res.stderr}")
                return None

            incident.repair_branch = branch_name
            incident.fix_status = "drafted"
            self.db.add(incident)
            await self.db.commit()

            return branch_name
        except Exception as e:
            logger.error(f"Failed to create healing worktree for incident {incident.id}: {e}")
            return None

    async def validate_and_propose(self, incident: IncidentMemory, github_service: Any) -> bool:
        if not incident.repair_branch:
            logger.error("No repair branch assigned to incident.")
            return False

        if not os.path.exists(self.worktree_dir):
            logger.error("Worktree directory not found.")
            return False

        try:
            worktree_backend_dir = os.path.join(self.worktree_dir, "backend")

            ruff_res = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "ruff", "check", "."],
                cwd=worktree_backend_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            pytest_res = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "pytest", "tests/test_autonomy_daemon.py"],
                cwd=worktree_backend_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            if ruff_res.returncode != 0 or pytest_res.returncode != 0:
                incident.fix_status = "validation_failed"
                safe_trace = pytest_res.stdout[-1000:] if pytest_res.stdout else ""
                incident.resolution_strategy = f"Shadow validation failed.\nRuff: {ruff_res.returncode}\nPytest: {pytest_res.returncode}\n{safe_trace}"
                self.db.add(incident)
                await self.db.commit()
                
                await asyncio.to_thread(subprocess.run, ["git", "worktree", "remove", "--force", self.worktree_dir], cwd=self.repo_dir, check=False)
                return False

            await asyncio.to_thread(
                subprocess.run, ["git", "add", "-u"], cwd=self.worktree_dir, check=False
            )
            commit_msg = f"fix(autonomy): resolve incident {incident.incident_type}\n\nIncident ID: {incident.id}"
            res = await asyncio.to_thread(
                subprocess.run,
                ["git", "commit", "-m", commit_msg],
                cwd=self.worktree_dir,
                capture_output=True,
                check=False,
            )

            if b"nothing to commit" not in res.stdout:
                await asyncio.to_thread(
                    subprocess.run,
                    ["git", "push", "-u", "origin", incident.repair_branch],
                    cwd=self.worktree_dir,
                    check=False,
                )

            prUrl = await github_service.create_pull_request(
                title=f"auto-fix: {incident.incident_type}",
                body=f"Automated resolution for incident {incident.id}.\n\n{incident.description}",
                head=incident.repair_branch,
                base="main",
            )

            if prUrl:
                incident.pr_url = prUrl
                incident.fix_status = "proposed"
            else:
                incident.fix_status = "pr_failed"
            
            self.db.add(incident)
            await self.db.commit()

            await asyncio.to_thread(subprocess.run, ["git", "worktree", "remove", "--force", self.worktree_dir], cwd=self.repo_dir, check=False)

            return prUrl is not None

        except Exception as e:
            logger.error(f"Git or validation command failed: {e}")
            await asyncio.to_thread(subprocess.run, ["git", "worktree", "remove", "--force", self.worktree_dir], cwd=self.repo_dir, check=False)
            return False
