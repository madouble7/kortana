"""
PR Creation Router for Kor'tana Autonomous System

Handles automatic PR creation from completed task branches.
"""

import os
from datetime import datetime
from typing import Any

import requests
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from logger import setup_logging
from models import GitHubTask
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from routers.code_reviewer import CodeReviewer
from routers.test_orchestrator import TestOrchestrator

router = APIRouter()
logger = setup_logging()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class PRCreationError(Exception):
    """Raised when PR creation fails"""

    pass


class PRCreator:
    """Automated PR creation from task branches"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token = GITHUB_TOKEN
        self.test_orchestrator = TestOrchestrator()
        self.code_reviewer = CodeReviewer()

    def _validate_token(self) -> bool:
        """Validate GitHub token is configured"""
        if not self.token:
            raise HTTPException(
                status_code=500, detail="GitHub token not configured for PR creation"
            )
        return True

    def _get_repo_info(self, repo: str):  # type: ignore[no-untyped-def]
        """Parse repo string into owner and name"""
        parts = repo.split("/")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail=f"Invalid repo format: {repo}")
        return parts[0], parts[1]

    def _generate_pr_description(  # type: ignore[no-untyped-def]
        self,
        task: GitHubTask,
        code_changes=None,
        test_results=None,
        review_results=None,
    ) -> str:
        """Generate PR description from task information"""
        description = f"""## Summary
- **Issue:** #{task.github_issue_number}
- **Status:** {task.status}
- **Priority:** {task.priority}

## Changes

{task.description or "No description provided."}

## Analysis

{task.analysis or "No analysis available."}

## Plan

{task.plan or "No plan available."}

## Files Changed

"""

        if code_changes:
            if code_changes.get("created"):
                description += "### Created\n"
                for f in code_changes["created"]:
                    description += f"- `{f}`\n"
                description += "\n"

            if code_changes.get("modified"):
                description += "### Modified\n"
                for f in code_changes["modified"]:
                    description += f"- `{f}`\n"
                description += "\n"

            if code_changes.get("deleted"):
                description += "### Deleted\n"
                for f in code_changes["deleted"]:
                    description += f"- `{f}`\n"
                description += "\n"
        else:
            description += "_Files changed information not available_\n\n"

        # Add test results if available
        if test_results:
            description += "## Testing\n\n"
            if test_results.get("success"):
                description += "✅ **All tests passed**\n\n"
            else:
                description += "❌ **Some tests failed**\n\n"

            description += f"- **Tests:** {test_results.get('tests_passed', 0)} passed, {test_results.get('tests_failed', 0)} failed\n"
            description += f"- **Coverage:** {test_results.get('coverage', 0.0):.1f}%\n"
            description += f"- **Linting:** {'✅ Passed' if test_results.get('linting_passed') else '❌ Failed'}\n"
            description += f"- **Type Check:** {'✅ Passed' if test_results.get('type_check_passed') else '❌ Failed'}\n"
            description += f"- **Duration:** {test_results.get('duration_ms', 0)}ms\n\n"
        else:
            description += """## Testing

- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] Edge cases considered

"""

        # Add code review results if available
        if review_results and review_results.get("success"):
            description += "## Code Review\n\n"
            score = review_results.get("score", 0)
            if score >= 8:
                description += f"🎉 **Score: {score}/10** - High quality code\n\n"
            elif score >= 6:
                description += (
                    f"👍 **Score: {score}/10** - Good code with minor improvements\n\n"
                )
            else:
                description += (
                    f"⚠️ **Score: {score}/10** - Needs significant improvements\n\n"
                )

            description += f"**Summary:** {review_results.get('summary', 'N/A')}\n\n"

            if review_results.get("strengths"):
                description += "**Strengths:**\n"
                for strength in review_results["strengths"][:3]:  # Limit to 3
                    description += f"- {strength}\n"
                description += "\n"

            recommendation = review_results.get("recommendation", "comment")
            if recommendation == "approve":
                description += "🤖 **Recommendation:** Auto-approve\n\n"
            elif recommendation == "request_changes":
                description += "🤖 **Recommendation:** Request changes\n\n"
            else:
                description += "🤖 **Recommendation:** Review comments\n\n"
        else:
            description += "## Code Review\n\n"
            description += "_Automated code review not performed_\n\n"

        description += """## Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes

---

*Generated by Kor'tana Autonomous System*
"""
        return description

    def _run_tests_for_task(self, task: GitHubTask) -> dict[str, Any]:
        """Run automated tests for a task"""
        try:
            logger.info(f"Running tests for task {task.id}")
            test_result = self.test_orchestrator.run_full_validation()

            return {
                "success": test_result["overall_status"] == "passed",
                "tests_passed": test_result["tests"].passed
                if test_result["tests"]
                else 0,
                "tests_failed": test_result["tests"].failed
                if test_result["tests"]
                else 0,
                "coverage": test_result["coverage"]["coverage"]
                if test_result["coverage"]
                else 0.0,
                "linting_passed": test_result["linting"]["passed"]
                if test_result["linting"]
                else False,
                "type_check_passed": test_result["type_checking"]["passed"]
                if test_result["type_checking"]
                else False,
                "duration_ms": test_result["duration_ms"],
                "details": test_result,
            }
        except Exception as e:
            logger.error(f"Test execution failed for task {task.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tests_passed": 0,
                "tests_failed": 0,
                "coverage": 0.0,
                "linting_passed": False,
                "type_check_passed": False,
                "duration_ms": 0,
            }

    def _review_code_for_task(self, task: GitHubTask) -> dict[str, Any]:
        """Perform code review for a task"""
        try:
            logger.info(f"Performing code review for task {task.id}")

            # Get code changes (simplified - in real implementation would get diff from GitHub)
            # For now, we'll do a basic review based on task description
            review = self.code_reviewer.generate_review(
                code=task.description or "No code provided", plan=task.plan or ""
            )

            # Parse the review JSON
            import json

            if isinstance(review, str):
                try:
                    review_data = json.loads(review)
                except json.JSONDecodeError:
                    review_data = {"summary": review, "overall_score": 5}
            else:
                review_data = review

            return {
                "success": True,
                "score": review_data.get("overall_score", 5),
                "recommendation": review_data.get("recommendation", "comment"),
                "summary": review_data.get("summary", "Review completed"),
                "strengths": review_data.get("strengths", []),
                "improvements": review_data.get("improvements", []),
            }
        except Exception as e:
            logger.error(f"Code review failed for task {task.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "score": 0,
                "recommendation": "comment",
                "summary": "Code review failed",
            }

    async def create_pr(
        self, task_id: str, run_tests: bool = True, run_review: bool = True
    ) -> dict[str, Any]:
        """Create a PR for a completed task with automated testing and review"""
        self._validate_token()

        result = await self.db.execute(
            select(GitHubTask).where(GitHubTask.id == task_id)
        )
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task must be completed before creating PR (current status: {task.status})",
            )

        if task.github_pr_number:
            raise HTTPException(
                status_code=400,
                detail=f"PR already created (PR #{task.github_pr_number})",
            )

        if not task.branch_name:
            raise HTTPException(status_code=400, detail="No branch name for task")

        owner, repo = self._get_repo_info(task.github_repo)  # type: ignore[arg-type]

        # Run automated tests if requested
        test_results = None
        if run_tests:
            logger.info(f"Running automated tests for task {task_id}")
            test_results = self._run_tests_for_task(task)

        # Perform code review if requested
        review_results = None
        if run_review:
            logger.info(f"Performing code review for task {task_id}")
            review_results = self._review_code_for_task(task)

        # Prepare PR data
        pr_title = f"feat: {task.title}"
        pr_body = self._generate_pr_description(
            task, test_results=test_results, review_results=review_results
        )

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

        pr_data = {
            "title": pr_title,
            "body": pr_body,
            "head": task.branch_name,
            "base": "main",
        }

        # Create PR
        create_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        try:
            response = requests.post(
                create_url, headers=headers, json=pr_data, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to create PR for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create PR: {str(e)}"
            )

        pr_result = response.json()
        pr_number = pr_result["number"]
        pr_url = pr_result["html_url"]

        # Post code review as comment if review was performed and successful
        if review_results and review_results.get("success") and run_review:
            try:
                review_comment = self.code_reviewer.create_review_comment(
                    review_results
                )
                comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
                comment_data = {"body": review_comment}

                comment_response = requests.post(
                    comment_url, headers=headers, json=comment_data, timeout=30
                )
                if comment_response.status_code == 201:
                    logger.info(f"Posted code review comment to PR #{pr_number}")
                else:
                    logger.warning(f"Failed to post review comment to PR #{pr_number}")
            except Exception as e:
                logger.error(f"Failed to post review comment: {str(e)}")

        # Update task with PR number
        task.github_pr_number = pr_number
        task.updated_at = datetime.utcnow()

        try:
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update task with PR number: {str(e)}")
            # PR was created but we couldn't update the task
            return {
                "message": "PR created but task update failed",
                "pr_number": pr_number,
                "pr_url": pr_url,
                "warning": "Task was not updated with PR number",
                "test_results": test_results,
                "review_results": review_results,
            }

        logger.info(f"PR #{pr_number} created for task {task_id}")

        return {
            "message": "PR created successfully with automated testing and review",
            "pr_number": pr_number,
            "pr_url": pr_url,
            "task_id": task_id,
            "test_results": test_results,
            "review_results": review_results,
        }

    async def create_pr_from_issue(
        self, issue_number: int, repo: str
    ) -> dict[str, Any]:
        """Create PR from a GitHub issue by finding its task"""
        self._validate_token()

        result = await self.db.execute(
            select(GitHubTask).where(
                GitHubTask.github_issue_number == issue_number,
                GitHubTask.github_repo == repo,
                GitHubTask.status == "completed",
            )
        )
        task = result.scalars().first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"No completed task found for issue #{issue_number} in {repo}",
            )

        return await self.create_pr(task.id)  # type: ignore[arg-type]


# Dependency
async def get_pr_creator(db: AsyncSession = Depends(get_db)) -> PRCreator:
    """Get PR creator instance"""
    return PRCreator(db)


@router.post("/create/{task_id}")
async def create_pr_endpoint(
    task_id: str,
    run_tests: bool = True,
    run_review: bool = True,
    pr_creator: PRCreator = Depends(get_pr_creator),
) -> dict[str, Any]:
    """Create a PR for a completed task with automated testing and review"""
    try:
        result = await pr_creator.create_pr(
            task_id, run_tests=run_tests, run_review=run_review
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PR creation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create/from-issue/{issue_number}")
async def create_pr_from_issue_endpoint(
    issue_number: int,
    repo: str,
    pr_creator: PRCreator = Depends(get_pr_creator),
) -> dict[str, Any]:
    """Create a PR from a GitHub issue number"""
    try:
        result = await pr_creator.create_pr_from_issue(issue_number, repo)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PR creation from issue failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_pr_status(
    task_id: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get PR status for a task"""
    result = await db.execute(select(GitHubTask).where(GitHubTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.github_pr_number:
        return {
            "task_id": task_id,
            "has_pr": False,
            "message": "No PR created yet",
        }

    # Get PR details from GitHub
    if not GITHUB_TOKEN:
        return {
            "task_id": task_id,
            "has_pr": True,
            "pr_number": task.github_pr_number,
            "message": "PR created but GitHub token not configured for details",
        }

    owner, repo = task.github_repo.split("/")  # type: ignore[union-attr]
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    pr_url = (
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{task.github_pr_number}"
    )

    try:
        response = requests.get(pr_url, headers=headers, timeout=10)
        if response.status_code == 200:
            pr_data = response.json()
            return {
                "task_id": task_id,
                "has_pr": True,
                "pr_number": task.github_pr_number,
                "pr_url": pr_data.get("html_url"),
                "state": pr_data.get("state"),
                "merged": pr_data.get("merged"),
                "title": pr_data.get("title"),
                "draft": pr_data.get("draft"),
            }
        else:
            return {
                "task_id": task_id,
                "has_pr": True,
                "pr_number": task.github_pr_number,
                "message": "Could not fetch PR details",
            }
    except Exception as e:
        return {
            "task_id": task_id,
            "has_pr": True,
            "pr_number": task.github_pr_number,
            "message": f"Error fetching PR details: {str(e)}",
        }


@router.get("/list/{repo}")
async def list_prs_for_repo(
    repo: str, state: str = "open", db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """List PRs created by the system for a repo"""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    owner, name = repo.split("/")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    prs_url = f"https://api.github.com/repos/{owner}/{name}/pulls?state={state}&head={owner}:feature/"

    try:
        response = requests.get(prs_url, headers=headers, timeout=10)
        response.raise_for_status()
        prs = response.json()

        # Filter to only PRs from feature branches (our format)
        feature_prs = [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "url": pr["html_url"],
                "draft": pr.get("draft", False),
            }
            for pr in prs
            if pr.get("head", {}).get("ref", "").startswith("feature/")
        ]

        return {
            "repo": repo,
            "state": state,
            "count": len(feature_prs),
            "prs": feature_prs,
        }
    except requests.RequestException as e:
        logger.error(f"Failed to list PRs for {repo}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list PRs: {str(e)}")


@router.post("/auto-create-all")
async def auto_create_prs_for_completed(
    repo: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Auto-create PRs for all completed tasks without PRs"""
    # Find completed tasks without PRs
    result = await db.execute(
        select(GitHubTask).where(
            GitHubTask.github_repo == repo,
            GitHubTask.status == "completed",
            GitHubTask.github_pr_number.is_(None),
        )
    )
    completed_tasks = result.scalars().all()

    if not completed_tasks:
        return {
            "message": "No completed tasks without PRs found",
            "repo": repo,
            "count": 0,
        }

    pr_creator = PRCreator(db)
    results = []

    for task in completed_tasks:
        try:
            result = await pr_creator.create_pr(
                task.id, run_tests=True, run_review=True
            )  # type: ignore[assignment, arg-type]
            results.append(
                {
                    "task_id": task.id,
                    "issue_number": task.github_issue_number,
                    "pr_number": result.get("pr_number"),  # type: ignore[attr-defined]
                    "success": True,
                    "test_results": result.get("test_results"),  # type: ignore[attr-defined]
                    "review_results": result.get("review_results"),  # type: ignore[attr-defined]
                }
            )
        except Exception as e:
            results.append(
                {
                    "task_id": task.id,
                    "issue_number": task.github_issue_number,
                    "error": str(e),
                    "success": False,
                }
            )

    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful

    return {
        "message": f"Processed {len(results)} tasks",
        "repo": repo,
        "successful": successful,
        "failed": failed,
        "results": results,
    }


@router.get("/health")
async def pr_health_check() -> dict[str, Any]:
    """Health check for PR creation service"""
    return {
        "status": "healthy",
        "service": "pr_creation",
        "timestamp": datetime.utcnow().isoformat(),
        "github_configured": bool(GITHUB_TOKEN),
    }
