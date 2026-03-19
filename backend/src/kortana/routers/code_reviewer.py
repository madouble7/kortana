"""
Code Review Module for KOR'TANA Autonomous System
Handles automated code review, security scanning, and approval logic
"""

import logging
import re

import httpx
from fastapi import APIRouter
from src.kortana.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class CodeReviewError(Exception):
    """Raised when code review fails"""

    pass


class CodeReviewer:
    """Performs automated code reviews using Gemini AI"""

    # Security patterns to check
    SECURITY_PATTERNS = {
        "sql_injection": r"(SELECT|INSERT|UPDATE|DELETE|execute|query|sql).*(['\"]|\+|f\"|format\(|\%)",
        "hardcoded_secrets": r"(password|api_key|token|secret)\s*=\s*['\"][^'\"]+['\"]",
        "unsafe_eval": r"(eval|exec|__import__)\s*\(",
        "insecure_deserialization": r"(pickle|yaml|eval)\.loads?",
    }

    def __init__(self, gemini_api_key: str | None = None):
        """Initialize code reviewer with Gemini API key"""
        self.gemini_api_key = gemini_api_key or get_settings().GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.timeout = 60

    def scan_for_security_issues(self, code: str) -> list[str]:
        """
        Scan code for common security issues

        Args:
            code: Source code to scan

        Returns:
            Flat list of security issues found
        """
        all_issues = []

        # Check for SQL injection patterns
        if re.search(self.SECURITY_PATTERNS["sql_injection"], code):
            all_issues.append("Potential SQL injection: Dynamic SQL construction detected")

        # Check for hardcoded secrets
        if re.search(self.SECURITY_PATTERNS["hardcoded_secrets"], code):
            all_issues.append("Hardcoded credentials: Passwords or tokens found in source code")

        # Check for unsafe eval
        if re.search(self.SECURITY_PATTERNS["unsafe_eval"], code):
            all_issues.append("Unsafe code execution: Use of eval/exec/import detected")

        # Check for insecure deserialization
        if re.search(self.SECURITY_PATTERNS["insecure_deserialization"], code):
            all_issues.append("Insecure deserialization: Unsafe pickle/yaml loading detected")

        return all_issues

    def check_code_quality(self, code: str) -> dict:
        """
        Basic code quality checks

        Args:
            code: Source code to check

        Returns:
            Quality metrics and issues
        """
        lines = code.split("\n")
        line_count = len(lines)
        empty_lines = sum(1 for line in lines if not line.strip())
        comment_ratio = (
            sum(1 for line in lines if line.strip().startswith("#")) / line_count
            if line_count > 0
            else 0
        )
        avg_line_length = sum(len(line) for line in lines) / line_count if line_count > 0 else 0

        # Long lines check
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]

        metrics = {
            "line_count": line_count,
            "total_lines": line_count,
            "empty_lines": empty_lines,
            "comment_ratio": comment_ratio,
            "average_line_length": avg_line_length,
            "long_lines": len(long_lines),
        }

        issues = []
        if len(long_lines) > 0:
            issues.append(
                {
                    "type": "Long lines",
                    "severity": "low",
                    "count": len(long_lines),
                    "recommendation": "Keep lines under 100 characters",
                }
            )

        commented_code = sum(
            1 for line in lines if line.strip().startswith("#") and len(line.strip()) > 2
        )
        if commented_code > line_count * 0.1:
            issues.append(
                {
                    "type": "Excessive comments",
                    "severity": "low",
                    "count": commented_code,
                    "recommendation": "Remove commented-out code",
                }
            )

        # For backward compatibility with tests expecting a flat structure
        result = metrics.copy()
        result["avg_line_length"] = avg_line_length  # Compatibility
        result["metrics"] = metrics
        result["issues"] = issues
        return result

    def should_auto_approve(self, review: dict) -> bool:
        """Determine if a review should be automatically approved"""
        score = review.get("score", 0)
        recommendation = review.get("recommendation", "comment")
        return score >= 8 and recommendation == "approve"

    def create_review_comment(self, review: dict) -> str:
        """Format review data into a GitHub markdown comment"""
        score = review.get("score", 0)
        summary = review.get("summary", "No summary provided")
        recommendation = review.get("recommendation", "comment")

        comment = "## KOR'TANA Automated Code Review\n\n"
        comment += f"**Overall Score: {score}/10**\n"
        comment += f"**Decision: {recommendation.upper()}**\n\n"
        comment += f"### Summary\n{summary}\n\n"

        if review.get("strengths"):
            comment += "### Strengths\n"
            for strength in review["strengths"]:
                comment += f"- {strength}\n"
            comment += "\n"

        if review.get("improvements"):
            comment += "### Suggested Improvements\n"
            for imp in review["improvements"]:
                if isinstance(imp, str):
                    comment += f"- {imp}\n"
                    continue
                area = imp.get("area", "Unknown")
                suggestion = imp.get("suggestion", "")
                severity = imp.get("severity", "low")
                comment += f"- **[{severity.upper()}] {area}**: {suggestion}\n"

        return comment

    def generate_review(self, code: str, plan: str = None) -> dict:
        """
        Generate detailed code review using Gemini

        Args:
            code: Source code to review
            plan: Implementation plan context

        Returns:
            Review feedback dict
        """
        try:
            prompt = f"""Review the following code and provide constructive feedback on:
1. Code quality and style
2. Potential bugs or issues
3. Performance considerations
4. Testing coverage
5. Documentation

Code to review:
```python
{code}
```

{"Plan context: " + plan if plan else ""}

Provide a JSON response ONLY with the following structure:
{{
    "score": <1-10>,
    "overall_score": <1-10>,
    "summary": "<brief summary>",
    "strengths": ["<strength1>", "<strength2>", ...],
    "improvements": [
        {{"area": "<area>", "severity": "low|medium|high", "suggestion": "<suggestion>"}},
        ...
    ],
    "recommendation": "approve|request_changes|comment"
}}"""

            # Call Gemini API
            url = f"{self.base_url}/gemini-pro:generateContent?key={self.gemini_api_key}"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                response.raise_for_status()

            # Extract response
            res_json = response.json()
            text_response = (
                res_json.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Try to extract JSON
            import json

            json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group(0))
                # Ensure 'score' exists if 'overall_score' does
                if "overall_score" in review_data and "score" not in review_data:
                    review_data["score"] = review_data["overall_score"]
                return review_data

            return {
                "score": 5,
                "summary": "Full review parsing failed",
                "text": text_response,
                "recommendation": "comment",
            }

        except Exception as e:
            logger.error(f"Error generating review: {e}")
            return {
                "score": 0,
                "summary": f"Error: {str(e)}",
                "recommendation": "comment",
            }

    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        review: dict,
        token: str = None,
        dry_run: bool = False,
        **kwargs,  # Accept extra args like 'github_token'
    ) -> dict:
        """
        Post code review as PR comment

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            review: Review feedback
            token: GitHub API token
            dry_run: If True, don't actually post

        Returns:
            Post result
        """
        try:
            github_token = token or kwargs.get("github_token") or get_settings().GITHUB_TOKEN

            comment = self.create_review_comment(review)

            if dry_run:
                logger.info(f"[DRY RUN] Would post review to PR #{pr_number}")
                return {
                    "dry_run": True,
                    "status": "would_post",
                    "pr_number": pr_number,
                }

            if not github_token:
                return {
                    "error": "GitHub token required",
                    "status": "failed",
                }

            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json={"body": comment},
                    headers=headers,
                )
                response.raise_for_status()

            logger.info(f"Posted review to PR #{pr_number}")
            return {
                "success": True,
                "pr_number": pr_number,
                "comment_id": response.json().get("id"),
            }

        except Exception as e:
            error_msg = f"Error posting review: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}


# FastAPI Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for code review service"""
    return {"status": "healthy", "service": "code-review"}


@router.post("/scan-security")
async def scan_security_api(code_data: dict):
    """Perform security vulnerability scan"""
    code = code_data.get("code", "")
    reviewer = CodeReviewer()
    issues = reviewer.scan_for_security_issues(code)
    return {"issues": issues, "success": True}


@router.post("/check-quality")
async def check_quality_api(code_data: dict):
    """Check code quality"""
    code = code_data.get("code", "")
    reviewer = CodeReviewer()
    return reviewer.check_code_quality(code)


@router.post("/generate-review")
async def generate_review_api(review_data: dict):
    """Generate Gemni code review"""
    code = review_data.get("code", "")
    plan = review_data.get("plan", "")
    reviewer = CodeReviewer()
    return await reviewer.generate_review(code, plan)


@router.post("/post-review")
async def post_review_api(post_data: dict):
    """Post review to GitHub"""
    reviewer = CodeReviewer()
    return await reviewer.post_review(
        owner=post_data.get("owner"),
        repo=post_data.get("repo"),
        pr_number=post_data.get("pr_number"),
        review=post_data.get("review"),
        token=post_data.get("token"),
    )


@router.post("/auto-approve")
async def auto_approve_api(review_data: dict):
    """Check if review should be auto-approved"""
    reviewer = CodeReviewer()
    should_approve = reviewer.should_auto_approve(review_data.get("review", {}))
    return {"should_approve": should_approve}
