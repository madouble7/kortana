from fastapi import APIRouter, HTTPException
import os
import requests
from typing import Optional

router = APIRouter()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")

@router.get("/repos/{owner}/{repo}/issues")
async def get_repo_issues(owner: str, repo: str, state: Optional[str] = "open"):
    """Fetch issues from a GitHub repository."""
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GitHub token not configured")

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch issues")

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
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch pull requests")

    return response.json()

@router.post("/analyze")
async def analyze_github_content(payload: dict):
    """Analyze GitHub content using Kor'tana's Gemini functions."""
    content = payload.get("content", "")
    content_type = payload.get("type", "issue")  # issue, pr, commit

    # Call the existing Gemini analyze endpoint
    gemini_payload = {"text": f"Analyze this GitHub {content_type}: {content}"}

    try:
        response = requests.post(f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=gemini_payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Gemini analysis failed", "status_code": response.status_code}
    except requests.RequestException as e:
        return {"error": f"Failed to connect to Gemini service: {str(e)}"}
