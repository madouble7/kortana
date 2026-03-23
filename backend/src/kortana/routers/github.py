import os
import time
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.kortana.config import get_settings
from src.kortana.cache import cache_result_async

router = APIRouter()

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


@router.get("/repos/{owner}/{repo}/issues")
@cache_result_async(ttl=60, key_prefix="github_issues")
async def get_repo_issues(
    owner: str, repo: str, state: str | None = "open", page: int = 1, per_page: int = 30
):
    """Fetch issues from a GitHub repository with pagination."""
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
    owner: str, repo: str, state: str | None = "open", page: int = 1, per_page: int = 30
):
    """Fetch pull requests from a GitHub repository with pagination."""
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
You are Kor'tana, an autonomous AI system analyzing GitHub issues and PRs.

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
        model = genai.GenerativeModel("gemini-pro")

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
