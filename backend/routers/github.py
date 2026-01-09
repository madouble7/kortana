import os
from datetime import datetime
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")


class GitHubAnalysisRequest(BaseModel):
    title: str
    body: str
    issue_number: int
    type: str = "issue"  # issue or pr
    author: Optional[str] = None
    created_at: Optional[str] = None


class GitHubAnalysisResponse(BaseModel):
    issue_number: int
    summary: str
    priority: str  # high, medium, low
    analysis: str
    suggested_actions: list[str]
    estimated_effort: str
    analyzed_at: str


@router.get("/repos/{owner}/{repo}/issues")
async def get_repo_issues(owner: str, repo: str, state: Optional[str] = "open"):
    """Fetch issues from a GitHub repository."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch issues"
        )

    return response.json()


@router.get("/repos/{owner}/{repo}/pulls")
async def get_repo_pulls(owner: str, repo: str, state: Optional[str] = "open"):
    """Fetch pull requests from a GitHub repository."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state={state}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch pull requests"
        )

    return response.json()


@router.post("/analyze")
async def analyze_github_issue(
    request: GitHubAnalysisRequest,
) -> GitHubAnalysisResponse:
    """Analyze GitHub issue/PR with Gemini and return structured analysis"""

    analysis_prompt = f"""
You are Kor'tana, an autonomous AI system analyzing GitHub issues and PRs.

Issue/PR: {request.type.upper()} #{request.issue_number}
Title: {request.title}
Author: {request.author or "Unknown"}
Created: {request.created_at or "Unknown"}

Content:
{request.body}

Please analyze this and provide:
1. A concise summary (1-2 sentences)
2. Priority level (high, medium, low)
3. Detailed analysis
4. Suggested actions (list of 3-5 actionable next steps)
5. Estimated effort to resolve (e.g., "2 hours", "1 day", "1 week")

Format your response as JSON with these exact keys:
{{
    "summary": "...",
    "priority": "high|medium|low",
    "analysis": "...",
    "suggested_actions": ["action1", "action2", ...],
    "estimated_effort": "..."
}}
"""

    try:
        # Call Gemini API
        import google.generativeai as genai

        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")

        response = model.generate_content(analysis_prompt)

        # Parse response
        import json
        import re

        # Extract JSON from response
        response_text = response.text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            analysis_data = json.loads(json_match.group())
        else:
            analysis_data = {
                "summary": response_text[:200],
                "priority": "medium",
                "analysis": response_text,
                "suggested_actions": [],
                "estimated_effort": "TBD",
            }

        return GitHubAnalysisResponse(
            issue_number=request.issue_number,
            summary=analysis_data.get("summary", ""),
            priority=analysis_data.get("priority", "medium"),
            analysis=analysis_data.get("analysis", ""),
            suggested_actions=analysis_data.get("suggested_actions", []),
            estimated_effort=analysis_data.get("estimated_effort", ""),
            analyzed_at=datetime.now().isoformat(),
        )

    except ImportError:
        # Fallback if google-generativeai not available
        return GitHubAnalysisResponse(
            issue_number=request.issue_number,
            summary="Analysis unavailable",
            priority="medium",
            analysis="Gemini API not configured. Set GEMINI_API_KEY environment variable.",
            suggested_actions=["Configure GEMINI_API_KEY"],
            estimated_effort="TBD",
            analyzed_at=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze")
async def analyze_github_content(payload: dict):
    """Legacy analyze endpoint for backward compatibility"""
