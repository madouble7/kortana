"""
GitHub Automation Engine - Enhanced issue analysis and PR automation
Handles smart issue routing, analysis, planning, and autonomous PR creation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from config import get_settings
from logger import log_error, log_request
from llm_router import get_llm_router


class GitHubIssue(BaseModel):
    """GitHub issue representation"""

    number: int
    title: str
    body: str
    author: str
    labels: list[str]
    created_at: datetime
    updated_at: datetime
    html_url: str


class IssueAnalysis(BaseModel):
    """Structured analysis of a GitHub issue"""

    priority: str  # low, medium, high, critical
    complexity: str  # trivial, simple, moderate, complex
    estimated_effort: str  # e.g., "1 hour", "2 days"
    skill_required: list[str]  # e.g., ["Python", "FastAPI"]
    suggested_approach: str
    potential_risks: list[str]
    success_criteria: list[str]


class ExecutionPlan(BaseModel):
    """Detailed execution plan for an issue"""

    steps: list[str]
    file_changes: list[str]
    tests_required: list[str]
    estimated_duration: str
    rollback_strategy: str


class GitHubAutomationEngine:
    """Autonomous GitHub issue handling and PR creation"""

    def __init__(self):
        self.settings = get_settings()
        self.llm = get_llm_router()
        self.github_token = self.settings.GITHUB_TOKEN
        self.github_owner = self.settings.GITHUB_OWNER
        self.github_repo = self.settings.GITHUB_REPO

        # Import GitHub client lazily
        try:
            from github import Github

            self.gh = Github(self.github_token)
        except ImportError:
            log_error("github", "PyGithub not installed")
            self.gh = None

    async def analyze_issue(self, issue: GitHubIssue) -> IssueAnalysis:
        """
        Use LLM to deeply analyze a GitHub issue
        Determines priority, complexity, and approach
        """
        analysis_prompt = f"""
Analyze this GitHub issue and provide structured analysis:

Title: {issue.title}
Author: {issue.author}
Labels: {', '.join(issue.labels) if issue.labels else 'none'}
Body:
{issue.body}

Return a JSON object with:
{{
  "priority": "low|medium|high|critical",
  "complexity": "trivial|simple|moderate|complex",
  "estimated_effort": "1 hour|1 day|3 days|1 week",
  "skill_required": ["Python", "FastAPI", ...],
  "suggested_approach": "A brief paragraph describing how to solve this",
  "potential_risks": ["Risk 1", "Risk 2"],
  "success_criteria": ["Criterion 1", "Criterion 2"]
}}

Only return valid JSON, no markdown or extra text.
"""

        try:
            response = await self.llm.generate(
                analysis_prompt, temperature=0.3, max_tokens=1500
            )

            # Parse JSON response
            import json

            analysis_dict = json.loads(response.content)
            return IssueAnalysis(**analysis_dict)
        except Exception as e:
            log_error(
                "issue_analysis",
                f"Failed to analyze issue #{issue.number}: {str(e)}",
            )
            # Return default analysis
            return IssueAnalysis(
                priority="medium",
                complexity="simple",
                estimated_effort="1 day",
                skill_required=["Python"],
                suggested_approach="Review the issue and implement a solution",
                potential_risks=[],
                success_criteria=["Issue resolved"],
            )

    async def create_execution_plan(
        self, issue: GitHubIssue, analysis: IssueAnalysis
    ) -> ExecutionPlan:
        """
        Create detailed execution plan for implementing the solution
        """
        plan_prompt = f"""
You are implementing a solution for this GitHub issue:

Title: {issue.title}
Priority: {analysis.priority}
Complexity: {analysis.complexity}
Suggested Approach: {analysis.suggested_approach}
Skills Required: {', '.join(analysis.skill_required)}

Create a JSON execution plan with:
{{
  "steps": [
    "Step 1: Description",
    "Step 2: Description",
    ...
  ],
  "file_changes": [
    "path/to/file1.py",
    "path/to/file2.py"
  ],
  "tests_required": [
    "Test case 1",
    "Test case 2"
  ],
  "estimated_duration": "2 hours|1 day|3 days",
  "rollback_strategy": "How to revert if something goes wrong"
}}

Only return valid JSON, no markdown.
"""

        try:
            response = await self.llm.generate(
                plan_prompt, temperature=0.3, max_tokens=2000
            )

            import json

            plan_dict = json.loads(response.content)
            return ExecutionPlan(**plan_dict)
        except Exception as e:
            log_error(
                "plan_creation",
                f"Failed to create plan for issue #{issue.number}: {str(e)}",
            )
            return ExecutionPlan(
                steps=["Review issue", "Implement solution", "Test changes"],
                file_changes=[],
                tests_required=["Unit tests"],
                estimated_duration="1 day",
                rollback_strategy="Revert commit",
            )

    async def generate_code(
        self,
        issue: GitHubIssue,
        analysis: IssueAnalysis,
        plan: ExecutionPlan,
        file_path: str,
    ) -> str:
        """
        Generate code for a specific file in the execution plan
        """
        code_prompt = f"""
Generate code to implement this issue:

Title: {issue.title}
Approach: {analysis.suggested_approach}
File: {file_path}

Requirements:
- Follow Python best practices
- Include proper error handling
- Add docstrings
- Consider performance

Return only the Python code, no markdown or explanations.
"""

        try:
            response = await self.llm.generate(
                code_prompt, temperature=0.5, max_tokens=3000
            )
            return response.content
        except Exception as e:
            log_error(
                "code_generation",
                f"Failed to generate code for {file_path}: {str(e)}",
            )
            return ""

    async def create_pull_request(
        self,
        issue_number: int,
        branch_name: str,
        title: str,
        description: str,
        analysis: IssueAnalysis,
        plan: ExecutionPlan,
    ) -> Optional[dict]:
        """
        Create a pull request for the solution
        """
        if not self.gh:
            log_error("github", "GitHub client not initialized")
            return None

        try:
            repo = self.gh.get_repo(f"{self.github_owner}/{self.github_repo}")

            pr_body = f"""
## Resolves #{issue_number}

### Analysis
- **Priority**: {analysis.priority}
- **Complexity**: {analysis.complexity}
- **Estimated Effort**: {analysis.estimated_effort}
- **Skills Used**: {', '.join(analysis.skill_required)}

### Approach
{analysis.suggested_approach}

### Risks
{chr(10).join(f'- {risk}' for risk in analysis.potential_risks) or 'None identified'}

### Success Criteria
{chr(10).join(f'- {criterion}' for criterion in analysis.success_criteria)}

### Implementation Steps
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(plan.steps))}

### Files Changed
{chr(10).join(f'- `{f}`' for f in plan.file_changes)}

### Testing
{chr(10).join(f'- {t}' for t in plan.tests_required)}

### Rollback Strategy
{plan.rollback_strategy}

---
*Created by Kor'tana autonomous system*
"""

            # Create PR via REST API
            pulls = repo.get_pulls(state="open", head=f"{self.github_owner}:{branch_name}")
            if pulls.totalCount == 0:
                pr = repo.create_pull(
                    title=title,
                    body=pr_body,
                    head=branch_name,
                    base="main",
                )

                log_request(
                    "github_pr",
                    f"Created PR #{pr.number} for issue #{issue_number}",
                    details={"pr_url": pr.html_url},
                )

                return {
                    "number": pr.number,
                    "url": pr.html_url,
                    "created_at": pr.created_at.isoformat(),
                }
            else:
                log_request(
                    "github_pr",
                    f"PR already exists for branch {branch_name}",
                )
                return None

        except Exception as e:
            log_error(
                "github_pr_creation",
                f"Failed to create PR for issue #{issue_number}: {str(e)}",
            )
            return None

    async def process_issue_webhook(self, payload: dict) -> dict:
        """
        Handle GitHub webhook for issue events
        """
        action = payload.get("action")
        issue_data = payload.get("issue", {})

        issue_number = issue_data.get("number")
        title = issue_data.get("title")
        body = issue_data.get("body", "")
        author = issue_data.get("user", {}).get("login")
        labels = [label.get("name") for label in issue_data.get("labels", [])]

        log_request(
            "github_webhook",
            f"Received issue event: {action} (issue #{issue_number})",
            details={"title": title, "author": author},
        )

        # Only process opened/edited issues that aren't drafts
        if action not in ["opened", "edited"]:
            return {"status": "skipped", "reason": f"action={action}"}

        if "draft" in labels or "wontfix" in labels or "duplicate" in labels:
            return {"status": "skipped", "reason": "excluded_label"}

        # Create issue object
        issue = GitHubIssue(
            number=issue_number,
            title=title,
            body=body,
            author=author,
            labels=labels,
            created_at=datetime.fromisoformat(
                issue_data.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                issue_data.get("updated_at", "").replace("Z", "+00:00")
            ),
            html_url=issue_data.get("html_url", ""),
        )

        # Analyze issue
        analysis = await self.analyze_issue(issue)

        # Skip trivial/low-priority issues
        if analysis.priority == "low" or analysis.complexity == "trivial":
            return {
                "status": "skipped",
                "reason": f"priority={analysis.priority}",
            }

        # Create execution plan
        plan = await self.create_execution_plan(issue, analysis)

        return {
            "status": "analyzed",
            "issue_number": issue_number,
            "priority": analysis.priority,
            "complexity": analysis.complexity,
            "estimated_effort": analysis.estimated_effort,
            "plan_steps": len(plan.steps),
            "files_to_change": len(plan.file_changes),
        }


# Global instance
_github_engine: Optional[GitHubAutomationEngine] = None


def get_github_engine() -> GitHubAutomationEngine:
    """Get or create GitHub automation engine singleton"""
    global _github_engine
    if _github_engine is None:
        _github_engine = GitHubAutomationEngine()
    return _github_engine
