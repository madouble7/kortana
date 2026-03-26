"""
GitHub Autonomy Service for Kor'tana
Manages the autonomous development loop: monitoring issues, planning, and executing changes.
"""

import inspect
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from src.kortana.http_client import get_http_client
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.gemini import gemini_service
from src.kortana.services.operator_directive_service import OperatorDirectiveService
from src.kortana.services.workspace_bridge_service import get_workspace_bridge

from src.kortana.config import get_settings

from .code_generator import CodeGenerator

logger = get_logger(__name__)
settings = get_settings()


class GitHubAutonomyService:
    """Service for autonomous GitHub-driven development"""

    def __init__(self, db_session=None):
        self.db = db_session
        self.code_gen = CodeGenerator()
        self.settings = get_settings()
        self.http_client = get_http_client()
        self.repo_root = Path(__file__).resolve().parents[4]

        # Get GitHub token from environment first, then fallback to settings
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            self.github_token = self.settings.GITHUB_TOKEN

        # Validate token is actually set (not placeholder)
        if self.github_token and self.github_token.startswith("your_"):
            logger.warning("GitHub token appears to be a placeholder, replacing with env var")
            self.github_token = os.getenv("GITHUB_TOKEN", "")

        self.repo_owner = os.getenv("GITHUB_OWNER") or self.settings.GITHUB_OWNER
        self.repo_name = os.getenv("GITHUB_REPO") or self.settings.GITHUB_REPO
        self.max_retries = self.settings.TASK_MAX_RETRIES

        logger.info(f"GitHubAutonomyService initialized: {self.repo_owner}/{self.repo_name}")
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

    @staticmethod
    def _extract_http_error_detail(exc: Exception) -> tuple[int | None, str]:
        """Extract status code and body from HTTP errors when available."""
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
            response = exc.response
            detail = response.text
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = payload.get("message") or payload.get("error") or detail
            except ValueError:
                pass
            return response.status_code, detail
        return None, str(exc)

    def _validate_token(self) -> None:
        """Validate GitHub token is configured"""
        # Reload token from environment to support test mocks
        self.github_token = os.getenv("GITHUB_TOKEN") or get_settings().GITHUB_TOKEN
        if not self.github_token:
            raise ValueError("GitHub token not configured")

    async def _operator_preamble(self) -> str:
        """Return active operator steering for prompt conditioning."""
        try:
            summary = await OperatorDirectiveService(self.db).get_active_summary()
            workspace_context = get_workspace_bridge().prompt_context()
            if summary.prompt_preamble and workspace_context:
                return f"{summary.prompt_preamble}\n{workspace_context}"
            if workspace_context:
                return workspace_context
            return summary.prompt_preamble
        except Exception as e:
            logger.debug(f"Operator guidance unavailable for prompt build: {e}")
            return ""

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
            response = await self.http_client.get(
                url, api_name="github_api", headers=headers, timeout=15
            )
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
        url = f"https://api.github.com/repos/{owner}/{name}/issues?state=open&per_page=50"

        try:
            # Use sync httpx client for Celery compatibility
            response = httpx.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            issues = response.json()
            logger.info(f"Fetched {len(issues)} issues from {owner}/{name}")
            return [{"number": issue["number"], "title": issue["title"]} for issue in issues]
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

        # 1. Analyze pending tasks - batch fetch and process
        stmt = select(GitHubTask).where(GitHubTask.status == "pending").limit(limit)
        result = await self._db_execute(stmt)
        pending = result.scalars().all()
        for task in pending:
            await self.analyze_task(task)

        # 2. Plan analyzed tasks - batch fetch and process
        stmt = select(GitHubTask).where(GitHubTask.status == "analyzed").limit(limit)
        result = await self._db_execute(stmt)
        analyzed = result.scalars().all()
        for task in analyzed:
            await self.plan_task(task)

        # 3. Execute planned tasks (only if autonomous mode is enabled) - batch fetch and process
        if (
            self.settings.ENVIRONMENT == "production"
            or os.getenv("KORTANA_AUTONOMOUS_MODE") == "true"
        ):
            stmt = select(GitHubTask).where(GitHubTask.status == "planning_complete").limit(limit)
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
            task = task_or_id  # Already have the task object, no additional query needed

        task.status = "analyzing"
        await self._db_commit()

        try:
            logger.info(f"Analyzing task #{task.github_issue_number}: {task.title}")
            operator_preamble = await self._operator_preamble()
            prompt = (
                f"{operator_preamble}\n\n" if operator_preamble else ""
            ) + (
                f"You are KOR'TANA PRIME, an autonomous AI architect modifying your own application (or another repository).\n"
                f"Analyze this issue and provide expert-level implementation insights. "
                f"If this is a [SELF-REPAIR] issue, you must diagnose the internal autonomy logic flaw causing the error and architect a structural fix.\n\n"
                f"Title: {task.title}\nDescription: {task.description}"
            )
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
            task = task_or_id  # Already have the task object, no additional query needed

        task.status = "planning"
        await self._db_commit()

        try:
            logger.info(f"Planning task #{task.github_issue_number}")
            operator_preamble = await self._operator_preamble()
            prompt = (
                f"{operator_preamble}\n\n" if operator_preamble else ""
            ) + (
                f"You are KOR'TANA PRIME, an autonomous AI entity architecting your own codebase. "
                f"Generate a detailed file-by-file implementation plan for this issue. "
                f"You MUST output ONLY a valid JSON object matching this schema:\n"
                f"{{\n"
                f'  "FILE_CHANGES": [\n'
                f"    {{\n"
                f'      "file": "path/to/file.py",\n'
                f'      "action": "create|modify|delete",\n'
                f'      "content": "raw code content here"\n'
                f"    }}\n"
                f"  ]\n"
                f"}}\n"
                f"Title: {task.title}\nAnalysis: {task.analysis}"
            )
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

    async def execute_task(self, task_or_id: GitHubTask | str, dry_run: bool = False) -> GitHubTask:
        """Execute the task: Create branch, apply changes, and commit"""
        if isinstance(task_or_id, str):
            stmt = select(GitHubTask).where(GitHubTask.id == task_or_id)
            result = await self._db_execute(stmt)
            task = result.scalar_one_or_none()
            if not task:
                raise ValueError("Task not found")
        else:
            task = task_or_id  # Already have the task object, no additional query needed

        task.status = "executing"
        await self._db_commit()

        try:
            logger.info(f"Executing task #{task.github_issue_number}")

            # 1. Create GitHub branch
            if not dry_run:
                if not await self._maybe_await(self._create_branch(task)):
                    raise Exception(task.error_message or "Failed to create GitHub branch")

            # 2. Use CodeGenerator to apply changes
            result = self.code_gen.generate_from_gemini_plan(
                task.plan, repo_path=str(self.repo_root), dry_run=dry_run
            )

            if result.get("errors"):
                raise Exception(f"Code generation errors: {result['errors']}")

            files_changed = [
                str(path)
                for path in (
                    result.get("created", [])
                    + result.get("modified", [])
                    + result.get("deleted", [])
                )
            ]
            task.code_changes = files_changed or None

            # 3. Commit changes to the branch (if not dry-run)
            if not dry_run:
                if files_changed:
                    commit_sha = await self._commit_branch_changes(task, files_changed)
                    if not commit_sha:
                        raise Exception("Failed to commit changes")
                    task.commit_sha = commit_sha

                    # 4. Push branch to GitHub
                    if not await self._push_branch(task):
                        raise Exception("Failed to push branch")

                    # 5. Create pull request
                    pr_number = await self._create_pull_request_for_branch(task)
                    if pr_number:
                        task.github_pr_number = pr_number
                        logger.info(f"Created PR #{pr_number} for task #{task.github_issue_number}")

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
            logger.error("GitHub token not configured for branch creation")
            return False

        try:
            owner, repo = task.github_repo.split("/")
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Get main branch SHA
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"
            try:
                ref_response = await self.http_client.get(
                    ref_url, api_name="github_api", headers=headers, timeout=10
                )
                if ref_response.status_code != 200:
                    logger.debug(
                        f"Main branch not found (status {ref_response.status_code}), trying master"
                    )
                    raise Exception("Main branch not found")
            except Exception as e:
                logger.debug(f"Getting main branch failed: {str(e)}, trying master branch")
                # Try master branch
                ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/master"
                ref_response = await self.http_client.get(
                    ref_url, api_name="github_api", headers=headers, timeout=10
                )
                if ref_response.status_code != 200:
                    task.error_message = (
                        f"Failed to get master branch ({ref_response.status_code}): "
                        f"{ref_response.text}"
                    )
                    logger.error(task.error_message)
                    return False

            # Parse and validate main_sha
            try:
                main_sha = ref_response.json()["object"]["sha"]
                logger.debug(f"Got base branch SHA: {main_sha[:8]}...")
            except (KeyError, ValueError) as e:
                task.error_message = f"Failed to parse branch SHA from response: {str(e)}"
                logger.error(f"Failed to parse branch SHA from response: {str(e)}")
                return False

            # Create branch (idempotent - handle existing branches)
            branch_data = {"ref": f"refs/heads/{task.branch_name}", "sha": main_sha}
            create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
            logger.info(f"Creating branch: {task.branch_name}")

            try:
                create_response = await self.http_client.post(
                    create_url,
                    api_name="github_api",
                    headers=headers,
                    json=branch_data,
                    timeout=10,
                )
            except Exception as e:
                status_code, detail = self._extract_http_error_detail(e)
                if status_code == 422:
                    logger.info(f"Branch already exists: {task.branch_name} (idempotent)")
                    return True

                if status_code is not None:
                    task.error_message = (
                        f"Branch creation failed with status {status_code}: {detail}"
                    )
                    logger.error(task.error_message)
                else:
                    task.error_message = f"Branch creation failed with exception: {detail}"
                    logger.error(task.error_message)
                return False

            # 201 = created, 422 = already exists (idempotent success)
            if create_response.status_code == 201:
                logger.info(f"Branch created successfully: {task.branch_name}")
                return True
            elif create_response.status_code == 422:
                logger.info(f"Branch already exists: {task.branch_name} (idempotent)")
                return True
            else:
                task.error_message = (
                    f"Branch creation failed with status "
                    f"{create_response.status_code}: {create_response.text}"
                )
                logger.error(task.error_message)
                return False
        except Exception as e:
            task.error_message = f"Branch creation failed with exception: {str(e)}"
            logger.error(task.error_message)
            return False

    async def _commit_branch_changes(
        self, task: GitHubTask, files_changed: list[Any]
    ) -> str | None:
        """Commit changed files to the task branch and return the new SHA."""
        try:
            # Ensure the task branch exists locally before staging changes.
            try:
                subprocess.run(
                    ["git", "checkout", task.branch_name],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info(f"Checked out branch: {task.branch_name}")
            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Local checkout missing for {task.branch_name}, bootstrapping branch: {e.stderr}"
                )
                try:
                    subprocess.run(
                        ["git", "fetch", "origin", task.branch_name],
                        cwd=self.repo_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    subprocess.run(
                        ["git", "checkout", "-B", task.branch_name, "FETCH_HEAD"],
                        cwd=self.repo_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info(f"Created local branch {task.branch_name} from remote branch")
                except subprocess.CalledProcessError:
                    try:
                        subprocess.run(
                            ["git", "fetch", "origin", "main"],
                            cwd=self.repo_root,
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        subprocess.run(
                            ["git", "checkout", "-B", task.branch_name, "origin/main"],
                            cwd=self.repo_root,
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        logger.info(f"Created local branch {task.branch_name} from origin/main")
                    except subprocess.CalledProcessError as bootstrap_error:
                        logger.error(
                            f"Failed to bootstrap branch {task.branch_name}: {bootstrap_error.stderr}"
                        )
                        return None

            # Stage the changed files on the task branch
            for file_path in files_changed:
                subprocess.run(
                    ["git", "add", str(file_path)],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )
                logger.debug(f"Staged file: {file_path}")

            # Create commit with message from issue/task
            commit_message = (
                f"Auto: Resolve issue #{task.github_issue_number}\n\n"
                f"Issue: {task.title}\n"
                f"Branch: {task.branch_name}"
            )

            subprocess.run(
                ["git", "commit", "--no-verify", "-m", commit_message],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )

            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            commit_sha = sha_result.stdout.strip()

            logger.info(f"Committed changes on {task.branch_name}: {commit_sha[:8]}...")
            return commit_sha or None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes on {task.branch_name}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Commit failed with exception: {str(e)}")
            return None

    async def _push_branch(self, task: GitHubTask) -> bool:
        """Push the task branch to GitHub with isolation guarantees."""
        try:
            owner, repo = task.github_repo.split("/")

            # Verify we're still on the task branch (safety check)
            branch_check = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            current_branch = branch_check.stdout.strip()

            if current_branch != task.branch_name:
                logger.error(
                    f"Not on task branch! Current: {current_branch}, Expected: {task.branch_name}"
                )
                # Try to recover by checking out the branch
                subprocess.run(
                    ["git", "checkout", task.branch_name],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                )
                logger.info(f"Recovered: checked out {task.branch_name}")

            # Push task branch to origin using explicit branch reference (isolated push)
            push_url = f"https://{self.github_token}@github.com/{owner}/{repo}.git"

            result = subprocess.run(
                [
                    "git",
                    "push",
                    "-u",
                    push_url,
                    f"{task.branch_name}:{task.branch_name}",
                ],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info(f"Pushed branch {task.branch_name}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch {task.branch_name}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Push failed with exception: {str(e)}")
            return False

    async def _create_pull_request_for_branch(self, task: GitHubTask) -> int | None:
        """Create a pull request for the branch"""
        try:
            owner, repo = task.github_repo.split("/")

            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            # Create PR from branch back to main
            pr_data = {
                "title": f"[AUTO] {task.title}",
                "body": f"Autonomous fix for issue #{task.github_issue_number}\n\nGenerated by KOR'TANA autonomy system",
                "head": task.branch_name,
                "base": "main",
            }

            # Fallback to master if main doesn't exist
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

            response = await self.http_client.post(
                url, api_name="github_api", headers=headers, json=pr_data, timeout=10
            )

            if response.status_code == 201:
                pr = response.json()
                pr_number = pr.get("number")
                logger.info(f"Created PR #{pr_number} for {task.branch_name}")
                return pr_number
            elif response.status_code == 422:
                # PR might already exist
                logger.warning(f"PR creation returned 422: {response.text}")
                return None
            else:
                logger.error(
                    f"PR creation failed with status {response.status_code}: {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"PR creation failed with exception: {str(e)}")
            return None

    def close(self):
        """Close database session safely"""
        if self.db:
            try:
                # Try to close gracefully
                if hasattr(self.db, "close"):
                    self.db.close()
            except Exception as e:
                logger.debug(f"Error closing database session: {e}")
