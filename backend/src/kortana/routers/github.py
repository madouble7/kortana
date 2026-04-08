import hashlib
import hmac
import logging
import os
import re
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Request
from pydantic import BaseModel

from src.kortana.cache import cache_result_async
from src.kortana.config import get_settings
from src.kortana.services.gemini_config import get_preferred_model_name

router = APIRouter()

# Only allow safe GitHub owner/repo name characters
_GITHUB_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,100}$")

# Rate limiting
RATE_LIMIT_CACHE = {}
RATE_LIMIT_PERIOD = 60  # seconds
RATE_LIMIT_REQUESTS = 60


def get_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token is not None:
        return token
    return get_settings().GITHUB_TOKEN


def get_gemini_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key is not None:
        return key
    return get_settings().GEMINI_API_KEY


def rate_limit_check(endpoint: str) -> bool:
    """Check if endpoint has exceeded rate limit"""
    now = time.time()
    if endpoint not in RATE_LIMIT_CACHE:
        RATE_LIMIT_CACHE[endpoint] = {"count": 0, "reset_at": now + RATE_LIMIT_PERIOD}

    cache = RATE_LIMIT_CACHE[endpoint]
    if now > cache["reset_at"]:
        cache["count"] = 0
        cache["reset_at"] = now + RATE_LIMIT_PERIOD

    cache["count"] += 1
    return cache["count"] <= RATE_LIMIT_REQUESTS


class GitHubAnalysisRequest(BaseModel):
    title: str
    body: str
    issue_number: int
    type: str = "issue"  # issue or pr
    author: str | None = None
    created_at: str | None = None


class GitHubAnalysisResponse(BaseModel):
    issue_number: int
    summary: str
    priority: str  # high, medium, low
    analysis: str
    suggested_actions: list[str]
    estimated_effort: str
    analyzed_at: str


def _validate_github_name(value: str, field: str) -> str:
    """Raise 422 if owner or repo contains unsafe characters."""
    if not _GITHUB_NAME_RE.match(value):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {field}: only alphanumeric, dash, dot, and underscore are allowed (max 100 chars)",
        )
    return value


@router.get("/repos/{owner}/{repo}/issues")
@cache_result_async(ttl=60, key_prefix="github_issues")
async def get_repo_issues(
    owner: str = Path(..., max_length=100),
    repo: str = Path(..., max_length=100),
    state: str | None = "open",
    page: int = 1,
    per_page: int = 30,
):
    """Fetch issues from a GitHub repository with pagination."""
    _validate_github_name(owner, "owner")
    _validate_github_name(repo, "repo")
    if not rate_limit_check(f"issues:{owner}/{repo}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    github_token = get_github_token()
    if not github_token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    # Validate inputs
    if per_page > 100:
        per_page = 100
    if page < 1:
        page = 1
    if state not in ["open", "closed", "all"]:
        state = "open"

    headers = {"Authorization": f"token {github_token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&page={page}&per_page={per_page}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            issues = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="GitHub API request timed out")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

    # Return structured response for test compatibility
    return {
        "issues": issues,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(issues)
        }
    }


@router.get("/repos/{owner}/{repo}/pulls")
@cache_result_async(ttl=60, key_prefix="github_pulls")
async def get_repo_pulls(
    owner: str = Path(..., max_length=100),
    repo: str = Path(..., max_length=100),
    state: str | None = "open",
    page: int = 1,
    per_page: int = 30,
):
    """Fetch pull requests from a GitHub repository with pagination."""
    _validate_github_name(owner, "owner")
    _validate_github_name(repo, "repo")
    if not rate_limit_check(f"pulls:{owner}/{repo}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    github_token = get_github_token()
    if not github_token:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    # Validate inputs
    if per_page > 100:
        per_page = 100
    if page < 1:
        page = 1
    if state not in ["open", "closed", "all"]:
        state = "open"

    headers = {"Authorization": f"token {github_token}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}&page={page}&per_page={per_page}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            pulls = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="GitHub API request timed out")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"GitHub API error: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PRs: {str(e)}")

    # Return structured response for test compatibility
    return {
        "pull_requests": pulls,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": len(pulls)
        }
    }


@router.post("/analyze")
async def analyze_github_issue(
    request_data: dict[str, Any],
) -> GitHubAnalysisResponse:
    """Analyze GitHub issue/PR with Gemini and return structured analysis"""

    gemini_api_key = get_gemini_api_key()
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    # Handle both structured GitHubAnalysisRequest and simplified {content, type}
    body = request_data.get("body") or request_data.get("content", "")
    title = request_data.get("title", "Untitled")
    issue_number = request_data.get("issue_number", 0)
    req_type = request_data.get("type", "issue")
    author = request_data.get("author", "Unknown")
    created_at = request_data.get("created_at", datetime.utcnow().isoformat())

    analysis_prompt = f"""
we are kor'tana, an autonomous ai system analyzing github issues and prs.

Issue/PR: {req_type.upper()} # {issue_number}
Title: {title}
Author: {author}
Created: {created_at}

Content:
{body}

Please analyze this and provide ONLY a JSON response (no markdown, no code blocks):
{{
    "summary": "1-2 sentence summary",
    "priority": "high|medium|low",
    "analysis": "Detailed analysis paragraph",
    "suggested_actions": ["action1", "action2", "action3"],
    "estimated_effort": "e.g., 2 hours or 1 day"
}}
"""

    try:
        import json
        import re

        import google.generativeai as genai

        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(get_preferred_model_name("gemini-pro"))

        response = model.generate_content(analysis_prompt, timeout=30)
        response_text = response.text
        # Try to extract JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            try:
                analysis_data = json.loads(json_match.group())
                return GitHubAnalysisResponse(
                    issue_number=issue_number,
                    summary=str(analysis_data.get("summary", ""))[:500],
                    priority=analysis_data.get("priority", "medium"),
                    analysis=str(analysis_data.get("analysis", ""))[:2000],
                    suggested_actions=list(analysis_data.get("suggested_actions", []))[:5],
                    estimated_effort=str(analysis_data.get("estimated_effort", ""))[:100],
                    analyzed_at=datetime.now().isoformat(),
                )
            except Exception:
                pass

        # Fallback
        return GitHubAnalysisResponse(
            issue_number=issue_number,
            summary=response_text[:200],
            priority="medium",
            analysis=response_text,
            suggested_actions=[],
            estimated_effort="TBD",
            analyzed_at=datetime.now().isoformat(),
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Gemini SDK not installed. Install google-generativeai package",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")





logger = logging.getLogger(__name__)

async def process_webhook_comment(
    repo_full_name: str,
    issue_number: int,
    comment_id: str,
    comment_url: str,
    body_text: str,
    author: str,
    delivery_id: str
):
    from src.kortana.database import SessionLocal
    from src.kortana.services.task_approval_service import TaskApprovalService
    from src.kortana.services.github_autonomy_service import GitHubAutonomyService
    from src.kortana.models import GitHubTask
    from sqlalchemy import select
    
    async with SessionLocal() as session:
        stmt = select(GitHubTask).where(
            GitHubTask.github_repo == repo_full_name,
            GitHubTask.github_issue_number == issue_number
        ).order_by(GitHubTask.created_at.desc())
        
        result = await session.execute(stmt)
        task = result.scalars().first()
        
        if not task:
            logger.info(f"Webhook ignored: no task for {repo_full_name}#{issue_number}")
            return
            
        if task.status not in ("waiting_for_approval", "waiting_for_ho"):
            logger.info(f"Webhook ignored: task {task.id} not awaiting approval")
            return

        approval_service = TaskApprovalService(session)
        github_service = GitHubAutonomyService(session)
        
        try:
            action = await approval_service.process_command_from_comment(
                task_id=str(task.id),
                body=body_text,
                reviewer=author,
                github_comment_id=comment_id,
                github_comment_url=comment_url,
                last_github_delivery_id=delivery_id
            )
        except ValueError as e:
            logger.debug(f"Webhook process_command skip: {e}")
            return
            
        if action == "approved":
            logger.info(f"Webhook: Task {task.id} approved by {author}")
            await github_service.post_issue_comment(task, f"✅ @{author} Phase 4 explicit approval confirmed (Webhook). Resuming execution.")
            await approval_service.mark_comment_seen(str(task.id), github_comment_id=comment_id, github_comment_url=comment_url, github_delivery_id=delivery_id)
        elif action == "rejected":
            logger.info(f"Webhook: Task {task.id} rejected by {author}")
            await github_service.post_issue_comment(task, f"❌ @{author} Phase 4 explicit rejection confirmed (Webhook). Halting.")
            await approval_service.mark_comment_seen(str(task.id), github_comment_id=comment_id, github_comment_url=comment_url, github_delivery_id=delivery_id)
        else:
            await approval_service.mark_comment_seen(str(task.id), github_comment_id=comment_id, github_comment_url=comment_url, github_delivery_id=delivery_id)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    signature = request.headers.get("x-hub-signature-256")
    event_type = request.headers.get("x-github-event")
    delivery_id = request.headers.get("x-github-delivery")
    
    settings = get_settings()
    webhook_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
    
    body = await request.body()
    
    if webhook_secret:
        if not signature:
            raise HTTPException(status_code=401, detail="Missing signature")
            
        expected_signature = "sha256=" + hmac.new(
            webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if event_type != "issue_comment":
        return {"status": "ignored", "reason": f"unhandled event type: {event_type}"}
        
    payload = await request.json()
    action = payload.get("action")
    if action not in ("created", "edited"):
        return {"status": "ignored", "reason": f"unhandled action: {action}"}
        
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    
    background_tasks.add_task(
        process_webhook_comment,
        repo_full_name=repository.get("full_name"),
        issue_number=issue.get("number"),
        comment_id=str(comment.get("id")),
        comment_url=comment.get("html_url"),
        body_text=comment.get("body"),
        author=comment.get("user", {}).get("login"),
        delivery_id=delivery_id or ""
    )
    
    return {"status": "accepted"}
