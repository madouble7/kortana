"""
GitHub Autonomy Service for Kor'tana
Manages the autonomous development loop: monitoring issues, planning, and executing changes.
"""

import inspect
import os
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select

from src.kortana.config import get_settings
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.gemini import gemini_service

from .code_generator import CodeGenerator

logger = get_logger(__name__)
settings = get_settings()


class GitHubAutonomyService:
    """Service for autonomous GitHub-driven development"""

    def __init__(self, db_session=None):
        self.db = db_session
        self.code_gen = CodeGenerator()
        self.settings = get_settings()

        # Get GitHub token from environment first, then fallback to settings
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            self.github_token = self.settings.GITHUB_TOKEN

        # Validate token is actually set (not placeholder)
        if self.github_token and self.github_token.startswith("your_"):
            logger.warning(
                "GitHub token appears to be a placeholder, replacing with env var"
            )
            self.github_token = os.getenv("GITHUB_TOKEN", "")

        self.repo_owner = os.getenv("GITHUB_OWNER") or self.settings.GITHUB_OWNER
        self.repo_name = os.getenv("GITHUB_REPO") or self.settings.GITHUB_REPO
        self.max_retries = self.settings.TASK_MAX_RETRIES

        logger.info(
            f"GitHubAutonomyService initialized: {self.repo_owner}/{self.repo_name}"
        )
        logger.debug(f"GitHub token present: {bool(self.github_token)}")

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        """Await value when needed, otherwise return it as-is."""
        if inspect.isawaitable(value):
            return await value
        return value

    async def _db_execute(self, stmt: Any) -> Any:
        """Execute a DB statement against async or sync-like test doubles."""
        if self.db is None:
            raise RuntimeError("Database session is not initialized")
        return await self._maybe_await(self.db.execute(stmt))

    async def _db_commit(self) -> None:
        """Commit DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.commit())

    async def _db_rollback(self) -> None:
        """Rollback DB transaction for async or sync-like test doubles."""
        if self.db is None:
            return
        await self._maybe_await(self.db.rollback())

    def _validate_token(self) -> None:
        """Validate GitHub token is configured"""
        # Reload token from environment to support test mocks
        self.github_token = os.getenv("GITHUB_TOKEN") or get_settings().GITHUB_TOKEN
        if not self.github_token:
            raise ValueError("GitHub token not configured")

    async def fetch_and_queue_issues(self, repo: str | None = None) -> list[GitHubTask]:
        """Fetch open issues from GitHub and queue them as tasks if not already present"""
        self._validate_token()

        owner, name = repo.split("/") if repo else (self.repo_owner, self.repo_name)
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await self._maybe_await(
                    client.get(url, headers=headers, timeout=15)
                )
                response.raise_for_status()
                issues = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            return []

        queued_tasks = []
        issue_numbers = [
            issue["number"] for issue in issues if "pull_request" not in issue
        ]

        if not issue_numbers:
            return []

        # Check existing tasks
        from sqlalchemy import select

        stmt = select(GitHubTask.github_issue_number).where(
            GitHubTask.github_issue_number.in_(issue_numbers),
            GitHubTask.github_repo == f"{owner}/{name}",
        )
        result = await self._db_execute(stmt)
        existing_issue_numbers = {row[0] for row in result.all()}

        for issue in issues:
            if "pull_request" in issue:
                continue

            if issue["number"] in existing_issue_numbers:
                continue

            task = GitHubTask(
                github_issue_number=issue["number"],
                github_repo=f"{owner}/{name}",
                title=issue["title"],
                description=issue.get("body") or "",
                status="pending",
                priority=self._determine_priority(issue),
                branch_name=self._generate_branch_name(issue["number"], issue["title"]),
            )

            self.db.add(task)
            queued_tasks.append(task)

        if queued_tasks:
            try:
                await self._db_commit()
                logger.info(f"Queued {len(queued_tasks)} new tasks from GitHub")
            except Exception as e:
                await self._db_rollback()
                logger.error(f"Failed to commit new tasks: {str(e)}")

        return queued_tasks

    def fetch_and_queue_issues_sync(self, repo: str | None = None) -> list[dict]:
        """Sync wrapper for fetch_and_queue_issues - fetches GitHub issues synchronously"""
        self._validate_token()

        owner, name = repo.split("/") if repo else (self.repo_owner, self.repo_name)
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = (
            f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"
        )

        try:
            # Use sync httpx client for Celery compatibility
            response = httpx.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            issues = response.json()
            logger.info(f"Fetched {len(issues)} issues from {owner}/{name}")
            return [
                {"number": issue["number"], "title": issue["title"]} for issue in issues
            ]
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            return []

    def _determine_priority(self, issue: dict[str, Any]) -> str:
        """Determine priority from labels"""
        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
        if any(label in ["critical", "p0", "urgent", "bug"] for label in labels):
            return "high"
        elif any(label in ["p2", "low", "chore"] for label in labels):
            return "low"
        return "medium"

    def _generate_branch_name(self, issue_num: int, title: str) -> str:
        """Generate safe branch name"""
        safe_title = "".join(c if c.isalnum() else "-" for c in title.lower())
        safe_title = "-".join(filter(None, safe_title.split("-")))[:50]
        return f"auto-fix/{issue_num}-{safe_title}"

    async def process_next_tasks(self, limit: int = 5):
        """Process tasks through the pipeline: Pending -> Analyzing -> Planning -> Executing"""
        from sqlalchemy import select

        # 1. Analyze pending tasks
        stmt = select(GitHubTask).where(GitHubTask.status == "pending").limit(limit)
        result = await self._db_execute(stmt)
        pending = result.scalars().all()
        for task in pending:
            await self.analyze_task(task)

        # 2. Plan analyzed tasks
        stmt = select(GitHubTask).where(GitHubTask.status == "analyzed").limit(limit)
        result = await self._db_execute(stmt)
        analyzed = result.scalars().all()
        for task in analyzed:
            await self.plan_task(task)

        # 3. Execute planned tasks (only if autonomous mode is enabled)
        if (
            self.settings.ENVIRONMENT == "production"
            or os.getenv("KORTANA_AUTONOMOUS_MODE") == "true"
        ):
            stmt = (
                select(GitHubTask)
                .where(GitHubTask.status == "planning_complete")
                .limit(limit)
            )
            result = await self._db_execute(stmt)
            planned = result.scalars().all()
            for task in planned:
                await self.execute_task(task)

    async def analyze_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Analyze task with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "analyzing"
        await self._db_commit()

        try:
            logger.info(f"Analyzing task #{task.github_issue_number}: {task.title}")
            prompt = f"Analyze this issue and provide implementation insights: \nTitle: {task.title}\nDescription: {task.description}"
            analysis = await self._maybe_await(gemini_service.analyze_text(prompt))
            task.analysis = analysis
            task.status = "analyzed"
            task.analyzed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            task.status = "pending"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self._db_commit()
        return task

    async def plan_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Generate implementation plan with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "planning"
        await self._db_commit()

        try:
            logger.info(f"Planning task #{task.github_issue_number}")
            prompt = f"Generate a detailed file-by-file implementation plan for this issue. Use the FILE_CHANGES format.\nTitle: {task.title}\nAnalysis: {task.analysis}"
            plan = await self._maybe_await(gemini_service.analyze_text(prompt))
            task.plan = plan
            task.status = "planning_complete"
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            task.status = "analyzed"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self._db_commit()
        return task

    async def execute_task(
        self, task_or_id: GitHubTask | str, dry_run: bool = False
    ) -> GitHubTask:
        """Execute the task: Create branch, apply changes, and commit"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "executing"
        await self._db_commit()

        try:
            logger.info(f"Executing task #{task.github_issue_number}")

            # 1. Create GitHub branch
            if not dry_run:
                if not await self._maybe_await(self._create_branch(task)):
                    raise Exception("Failed to create GitHub branch")

            # 2. Use CodeGenerator to apply changes
            result = self.code_gen.generate_from_gemini_plan(
                task.plan, repo_path=".", dry_run=dry_run
            )

            if result.get("errors"):
                raise Exception(f"Code generation errors: {result['errors']}")

            task.status = "executed"
            task.executed_at = datetime.utcnow()
            await self._db_commit()
            return task
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            task.status = "planning_complete"
            task.error_message = str(e)
            task.error_count = (task.error_count or 0) + 1
            if task.error_count >= self.max_retries:
                task.status = "failed"
            await self._db_commit()
            raise

    async def _create_branch(self, task: GitHubTask) -> bool:
        """Create GitHub branch for task using async httpx"""
        if not self.github_token:
            return False

        try:
            owner, repo = task.github_repo.split("/")
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with httpx.AsyncClient() as client:
                # Get main branch SHA
                ref_url = (
                    f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"
                )
                ref_response = await self._maybe_await(
                    client.get(ref_url, headers=headers, timeout=10)
                )

                if ref_response.status_code != 200:
                    # Try master branch
                    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
                    ref_response = await self._maybe_await(
                        client.get(ref_url, headers=headers, timeout=10)
                    )
                    if ref_response.status_code != 200:
                        return False

                main_sha = ref_response.json()["object"]["sha"]

                # Create branch
                branch_data = {"ref": f"refs/heads/{task.branch_name}", "sha": main_sha}
                create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
                create_response = await self._maybe_await(
                    client.post(
                        create_url, headers=headers, json=branch_data, timeout=10
                    )
                )

                return create_response.status_code == 201
        except Exception as e:
            logger.error(f"Branch creation failed: {str(e)}")
            return False

    def close(self):
        """Close database session safely"""
        if self.db:
            try:
                # Try to close gracefully
                if hasattr(self.db, "close"):
                    self.db.close()
            except Exception as e:
                logger.debug(f"Error closing database session: {e}")
