import os
import time
from datetime import datetime

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")

# Rate limiting
RATE_LIMIT_CACHE = {}
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_PERIOD = 60  # seconds


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
async def get_repo_issues(
    owner: str, repo: str, state: str | None = "open", page: int = 1, per_page: int = 30
):
    """Fetch issues from a GitHub repository with pagination."""
    if not rate_limit_check(f"issues:{owner}/{repo}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    # Validate inputs
    if per_page > 100:
        per_page = 100
    if page < 1:
        page = 1
    if state not in ["open", "closed", "all"]:
        state = "open"

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&page={page}&per_page={per_page}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="GitHub API request timed out")
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(
            status_code=response.status_code, detail=f"GitHub API error: {response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

    issues = response.json()

    # Return issues directly for frontend compatibility
    return issues


@router.get("/repos/{owner}/{repo}/pulls")
async def get_repo_pulls(
    owner: str, repo: str, state: str | None = "open", page: int = 1, per_page: int = 30
):
    """Fetch pull requests from a GitHub repository with pagination."""
    if not rate_limit_check(f"pulls:{owner}/{repo}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    # Validate inputs
    if per_page > 100:
        per_page = 100
    if page < 1:
        page = 1
    if state not in ["open", "closed", "all"]:
        state = "open"

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}&page={page}&per_page={per_page}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="GitHub API request timed out")
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        raise HTTPException(
            status_code=response.status_code, detail=f"GitHub API error: {response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PRs: {str(e)}")

    pulls = response.json()

    # Return pulls directly for frontend compatibility
    return pulls


@router.post("/analyze")
async def analyze_github_issue(
    request: GitHubAnalysisRequest,
) -> GitHubAnalysisResponse:
    """Analyze GitHub issue/PR with Gemini and return structured analysis"""

    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    analysis_prompt = f"""
You are Kor'tana, an autonomous AI system analyzing GitHub issues and PRs.

Issue/PR: {request.type.upper()} #{request.issue_number}
Title: {request.title}
Author: {request.author or "Unknown"}
Created: {request.created_at or "Unknown"}

Content:
{request.body}

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

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")

        response = model.generate_content(analysis_prompt, timeout=30)
        response_text = response.text

        # Try to extract JSON
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            try:
                analysis_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis_data = {
                    "summary": response_text[:200],
                    "priority": "medium",
                    "analysis": response_text,
                    "suggested_actions": [],
                    "estimated_effort": "TBD",
                }
        else:
            analysis_data = {
                "summary": response_text[:200],
                "priority": "medium",
                "analysis": response_text,
                "suggested_actions": [],
                "estimated_effort": "TBD",
            }

        # Validate response
        for key in ["summary", "priority", "analysis", "suggested_actions", "estimated_effort"]:
            if key not in analysis_data:
                analysis_data[key] = "" if key != "suggested_actions" else []

        return GitHubAnalysisResponse(
            issue_number=request.issue_number,
            summary=str(analysis_data.get("summary", ""))[:500],
            priority=analysis_data.get("priority", "medium"),
            analysis=str(analysis_data.get("analysis", ""))[:2000],
            suggested_actions=list(analysis_data.get("suggested_actions", []))[:5],
            estimated_effort=str(analysis_data.get("estimated_effort", ""))[:100],
            analyzed_at=datetime.now().isoformat(),
        )

    except ImportError:
        raise HTTPException(
            status_code=500, detail="Gemini SDK not installed. Install google-generativeai package"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
