"""
Code Review Module for KOR'TANA Autonomous System
Handles automated code review, security scanning, and approval logic
"""

import logging
import os
import re

import requests
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


class CodeReviewError(Exception):
    """Raised when code review fails"""

    pass


class CodeReviewer:
    """Performs automated code reviews using Gemini AI"""

    # Security patterns to check
    SECURITY_PATTERNS = {
        "sql_injection": r"(execute|query|sql)\s*\(\s*['\"].*\$|f\"|format\(",
        "hardcoded_secrets": r"(password|api_key|token|secret)\s*=\s*['\"][^'\"]+['\"]",
        "unsafe_eval": r"(eval|exec|__import__)\s*\(",
        "insecure_deserialization": r"(pickle|yaml|eval)\.loads?",
    }

    def __init__(self, gemini_api_key: str | None = None):
        """Initialize code reviewer with Gemini API key"""
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.timeout = 60

    def scan_for_security_issues(self, code: str) -> dict:
        """
        Scan code for common security issues

        Args:
            code: Source code to scan

        Returns:
            Security issues found
        """
        issues = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        # Check for SQL injection patterns
        if re.search(self.SECURITY_PATTERNS["sql_injection"], code):
            issues["high"].append(
                {
                    "type": "Potential SQL injection",
                    "description": "Dynamic SQL construction detected",
                    "recommendation": "Use parameterized queries",
                }
            )

        # Check for hardcoded secrets
        if re.search(self.SECURITY_PATTERNS["hardcoded_secrets"], code):
            issues["critical"].append(
                {
                    "type": "Hardcoded credentials",
                    "description": "Credentials found in source code",
                    "recommendation": "Use environment variables or secrets management",
                }
            )

        # Check for unsafe eval
        if re.search(self.SECURITY_PATTERNS["unsafe_eval"], code):
            issues["critical"].append(
                {
                    "type": "Unsafe code execution",
                    "description": "Use of eval/exec/import detected",
                    "recommendation": "Avoid dynamic code execution",
                }
            )

        # Check for insecure deserialization
        if re.search(self.SECURITY_PATTERNS["insecure_deserialization"], code):
            issues["high"].append(
                {
                    "type": "Insecure deserialization",
                    "description": "Unsafe deserialization detected",
                    "recommendation": "Use safe serialization formats like JSON",
                }
            )

        return issues

    def check_code_quality(self, code: str) -> dict:
        """
        Basic code quality checks

        Args:
            code: Source code to check

        Returns:
            Quality metrics
        """
        lines = code.split("\n")
        metrics = {
            "total_lines": len(lines),
            "empty_lines": sum(1 for line in lines if not line.strip()),
            "comment_ratio": sum(1 for line in lines if line.strip().startswith("#")) / len(lines)
            if lines
            else 0,
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
        }

        issues = []

        # Check for overly long lines
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            issues.append(
                {
                    "type": "Long lines",
                    "severity": "low",
                    "count": len(long_lines),
                    "recommendation": "Keep lines under 100 characters",
                }
            )

        # Check for commented code
        commented_code = sum(
            1 for line in lines if line.strip().startswith("#") and len(line.strip()) > 2
        )
        if commented_code > len(lines) * 0.1:
            issues.append(
                {
                    "type": "Excessive comments",
                    "severity": "low",
                    "count": commented_code,
                    "recommendation": "Remove commented-out code",
                }
            )

        return {
            "metrics": metrics,
            "issues": issues,
        }

    def generate_review(self, code: str, plan: str = None) -> str:
        """
        Generate detailed code review using Gemini

        Args:
            code: Source code to review
            plan: Implementation plan context

        Returns:
            Review feedback
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

Provide a JSON response with the following structure:
{{
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
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Extract response
            result = response.json()
            text_response = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Try to extract JSON
            json_match = re.search(r"\{.*\}", text_response, re.DOTALL)
            if json_match:
                return json_match.group(0)

            return text_response

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating review: {e}")
            raise CodeReviewError(f"Failed to generate review: {e}") from e

    def should_auto_approve(self, review: dict) -> bool:
        """
        Determine if code should be auto-approved

        Args:
            review: Review feedback

        Returns:
            True if code should be auto-approved
        """
        try:
            score = review.get("overall_score", 0)
            recommendation = review.get("recommendation", "comment")

            # Auto-approve if high score and no critical issues
            return score >= 8 and recommendation == "approve"
        except Exception as e:
            logger.error(f"Error determining auto-approval: {e}")
            return False

    def create_review_comment(self, review: dict) -> str:
        """
        Create a PR comment from review

        Args:
            review: Review feedback

        Returns:
            Formatted comment
        """
        try:
            comment = f"""## 🤖 Automated Code Review

**Overall Score:** {review.get("overall_score", "N/A")}/10

**Summary:** {review.get("summary", "N/A")}

### ✅ Strengths
"""
            for strength in review.get("strengths", []):
                comment += f"- {strength}\n"

            comment += "\n### 📝 Suggested Improvements\n"
            for improvement in review.get("improvements", []):
                severity = improvement.get("severity", "medium").upper()
                comment += f"- [{severity}] {improvement.get('area', 'N/A')}: {improvement.get('suggestion', 'N/A')}\n"

            recommendation = review.get("recommendation", "comment").upper()
            comment += f"\n**Recommendation:** {recommendation}\n"
            comment += "\n*This review was generated by KOR'TANA Autonomous System*"

            return comment

        except Exception as e:
            logger.error(f"Error creating review comment: {e}")
            return "Error generating review comment"

    def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        review: dict,
        github_token: str = None,
        dry_run: bool = False,
    ) -> dict:
        """
        Post code review as PR comment

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            review: Review feedback
            github_token: GitHub API token
            dry_run: If True, don't actually post

        Returns:
            Post result
        """
        try:
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

            response = requests.post(
                url,
                json={"body": comment},
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            logger.info(f"Posted review to PR #{pr_number}")
            return {
                "success": True,
                "pr_number": pr_number,
                "comment_id": response.json().get("id"),
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"GitHub API error posting review: {e}"
            logger.error(error_msg)
            raise CodeReviewError(error_msg) from e


# FastAPI Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for code review service"""
    return {"status": "healthy", "service": "code-review"}


@router.post("/analyze")
async def analyze_code(code: str, plan: str = ""):
    """Analyze code for quality and security"""
    try:
        reviewer = CodeReviewer()
        security_issues = reviewer.scan_for_security_issues(code)
        quality = reviewer.check_code_quality(code)

        return {
            "security_issues": security_issues,
            "code_quality": quality,
            "success": True,
        }
    except CodeReviewError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/security")
async def security_scan(code: str):
    """Perform security vulnerability scan"""
    try:
        reviewer = CodeReviewer()
        issues = reviewer.scan_for_security_issues(code)

        return {
            "issues": issues,
            "critical": sum(1 for i in issues if "critical" in str(i).lower()),
            "success": True,
        }
    except CodeReviewError as e:
        raise HTTPException(status_code=400, detail=str(e))
