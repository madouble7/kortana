"""
GitHub Autonomy Service for Kor'tana
Manages the autonomous development loop: monitoring issues, planning, and executing changes.
"""

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
        self.github_token = os.getenv("GITHUB_TOKEN") or self.settings.GITHUB_TOKEN
        self.repo_owner = self.settings.GITHUB_OWNER
        self.repo_name = self.settings.GITHUB_REPO
        self.max_retries = self.settings.TASK_MAX_RETRIES

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
        url = f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                issues = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch GitHub issues: {str(e)}")
            return []

        queued_tasks = []
        issue_numbers = [issue["number"] for issue in issues if "pull_request" not in issue]

        if not issue_numbers:
            return []

        # Check existing tasks
        from sqlalchemy import select

        stmt = select(GitHubTask.github_issue_number).where(
            GitHubTask.github_issue_number.in_(issue_numbers),
            GitHubTask.github_repo == f"{owner}/{name}",
        )
        result = await self.db.execute(stmt)
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
                await self.db.commit()
                logger.info(f"Queued {len(queued_tasks)} new tasks from GitHub")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to commit new tasks: {str(e)}")

        return queued_tasks

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
        result = await self.db.execute(stmt)
        pending = result.scalars().all()
        for task in pending:
            await self.analyze_task(task)

        # 2. Plan analyzed tasks
        stmt = select(GitHubTask).where(GitHubTask.status == "analyzed").limit(limit)
        result = await self.db.execute(stmt)
        analyzed = result.scalars().all()
        for task in analyzed:
            await self.plan_task(task)

        # 3. Execute planned tasks (only if autonomous mode is enabled)
        if (
            self.settings.ENVIRONMENT == "production"
            or os.getenv("KORTANA_AUTONOMOUS_MODE") == "true"
        ):
            stmt = select(GitHubTask).where(GitHubTask.status == "planning_complete").limit(limit)
            result = await self.db.execute(stmt)
            planned = result.scalars().all()
            for task in planned:
                await self.execute_task(task)

    async def analyze_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Analyze task with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self.db.execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "analyzing"
        await self.db.commit()

        try:
            logger.info(f"Analyzing task #{task.github_issue_number}: {task.title}")
            prompt = f"Analyze this issue and provide implementation insights: \nTitle: {task.title}\nDescription: {task.description}"
            analysis = await gemini_service.analyze_text(prompt)
            task.analysis = analysis
            task.status = "analyzed"
            task.analyzed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            task.status = "pending"
            task.error_message = str(e)
            task.error_count += 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self.db.commit()
        return task

    async def plan_task(self, task_or_id: GitHubTask | str) -> GitHubTask:
        """Generate implementation plan with Gemini"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self.db.execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "planning"
        await self.db.commit()

        try:
            logger.info(f"Planning task #{task.github_issue_number}")
            prompt = f"Generate a detailed file-by-file implementation plan for this issue. Use the FILE_CHANGES format.\nTitle: {task.title}\nAnalysis: {task.analysis}"
            plan = await gemini_service.analyze_text(prompt)
            task.plan = plan
            task.status = "planning_complete"
        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            task.status = "analyzed"
            task.error_message = str(e)
            task.error_count += 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self.db.commit()
        return task

    async def execute_task(self, task_or_id: GitHubTask | str, dry_run: bool = False) -> GitHubTask:
        """Execute the task: Create branch, apply changes, and commit"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self.db.execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id

        task.status = "executing"
        await self.db.commit()

        try:
            logger.info(f"Executing task #{task.github_issue_number}")

            # 1. Create GitHub branch
            if not dry_run:
                if not await self._create_branch(task):
                    raise Exception("Failed to create GitHub branch")

            # 2. Use CodeGenerator to apply changes
            result = self.code_gen.generate_from_gemini_plan(
                task.plan, repo_path=".", dry_run=dry_run
            )

            if result.get("errors"):
                raise Exception(f"Code generation errors: {result['errors']}")

            task.status = "executed"
            task.executed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            task.status = "planning_complete"
            task.error_message = str(e)
            task.error_count += 1
            if task.error_count >= self.max_retries:
                task.status = "failed"

        await self.db.commit()
        return task

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
                ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"
                ref_response = await client.get(ref_url, headers=headers, timeout=10)

                if ref_response.status_code != 200:
                    # Try master branch
                    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
                    ref_response = await client.get(ref_url, headers=headers, timeout=10)
                    if ref_response.status_code != 200:
                        return False

                main_sha = ref_response.json()["object"]["sha"]

                # Create branch
                branch_data = {"ref": f"refs/heads/{task.branch_name}", "sha": main_sha}
                create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
                create_response = await client.post(
                    create_url, headers=headers, json=branch_data, timeout=10
                )

                return create_response.status_code == 201
        except Exception as e:
            logger.error(f"Branch creation failed: {str(e)}")
            return False

    def close(self):
        self.db.close()
