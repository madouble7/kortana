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
    - Never writes to main.
    - Creates auto-fix/<incident-type>-<timestamp> branches.
    - Runs ruff and pytest locally before committing or creating PR.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../..")
        )

    def evaluate_incident(self, incident: IncidentMemory) -> bool:
        """
        Determines if the system is allowed to attempt self-healing on this incident.
        """
        if incident.resolved:
            return False

        # Only allow known-safe classes for initial Vector Alpha roll-out
        allowed_types = ["daemon_crash", "task_failure", "broken_test", "test_failure"]
        if incident.incident_type not in allowed_types:
            return False

        if not incident.description:
            return False

        # Avoid sensitive keywords
        sensitive_keywords = ["auth", "billing", "secret", "deploy", "config", "token"]
        desc_lower = incident.description.lower()
        if any(sk in desc_lower for sk in sensitive_keywords):
            return False

        return True

    async def create_healing_branch(self, incident: IncidentMemory) -> Optional[str]:
        """
        Spawns a transient Git branch mapped to this incident.
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            sanitized_type = incident.incident_type.replace("_", "-")
            branch_name = f"auto-fix/{sanitized_type}-{timestamp}"

            # Hard fail if repo is not clean to prevent sweeping unintended changes
            status_res = await asyncio.to_thread(
                subprocess.run,
                ["git", "status", "--porcelain"],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )
            if status_res.stdout.strip():
                logger.error("Repo is not clean. Vector Alpha requires a clean worktree.")
                return None

            # Create and checkout branch
            res = await asyncio.to_thread(
                subprocess.run,
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )
            if res.returncode != 0:
                logger.error(f"Failed to create branch: {res.stderr}")
                return None

            incident.repair_branch = branch_name
            incident.fix_status = "drafted"
            self.db.add(incident)
            await self.db.commit()

            return branch_name
        except Exception as e:
            logger.error(
                f"Failed to create healing branch for incident {incident.id}: {e}"
            )
            return None

    async def validate_and_propose(
        self, incident: IncidentMemory, github_service: Any
    ) -> bool:
        """
        Shadow-first validation:
        1. Run ruff
        2. Run pytest
        3. If pass, push and use GithubAutonomyService to create PR.
        """
        if not incident.repair_branch:
            logger.error("No repair branch assigned to incident.")
            return False

        try:
            backend_dir = os.path.join(self.repo_dir, "backend")

            # 1. Validation Run: Ruff
            ruff_res = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "ruff", "check", "."],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            # 2. Validation Run: Pytest
            pytest_res = await asyncio.to_thread(
                subprocess.run,
                ["python", "-m", "pytest", "tests/test_autonomy_daemon.py"],
                cwd=backend_dir,
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
                # Revert to main
                await asyncio.to_thread(
                    subprocess.run,
                    ["git", "checkout", "main"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    check=False,
                )
                return False

            # If passed, commit the patch
            # Stage only modified tracked files, protecting against untracked files
            await asyncio.to_thread(
                subprocess.run, ["git", "add", "-u"], cwd=self.repo_dir, check=False
            )
            commit_msg = f"fix(autonomy): resolve incident {incident.incident_type}\n\nIncident ID: {incident.id}"
            res = await asyncio.to_thread(
                subprocess.run,
                ["git", "commit", "-m", commit_msg],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )

            if b"nothing to commit" not in res.stdout:
                # Push branch
                await asyncio.to_thread(
                    subprocess.run,
                    ["git", "push", "-u", "origin", incident.repair_branch],
                    cwd=self.repo_dir,
                    check=False,
                )

            # 3. Create PR (using GithubAutonomyService)
            # using internal method or we need to update github_autonomy_service.py correctly
            prUrl = await github_service.create_pull_request(
                title=f"auto-fix: {incident.incident_type}",
                body=f"Automated resolution for incident {incident.id}.\n\n{incident.description}",
                head=incident.repair_branch,
                base="main",
            )

            if prUrl:
                incident.pr_url = prUrl
                incident.fix_status = "proposed"
                self.db.add(incident)
                await self.db.commit()
            else:
                incident.fix_status = "pr_failed"
                self.db.add(incident)
                await self.db.commit()

            # Return to main
            await asyncio.to_thread(
                subprocess.run,
                ["git", "checkout", "main"],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )

            return prUrl is not None

        except Exception as e:
            logger.error(f"Git or validation command failed: {e}")
            await asyncio.to_thread(
                subprocess.run,
                ["git", "checkout", "main"],
                cwd=self.repo_dir,
                capture_output=True,
                check=False,
            )
            return False
