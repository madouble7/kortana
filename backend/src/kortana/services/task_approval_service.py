"""
Task approval service.

Provides a first-class approval queue for GitHub autonomy tasks. Approval can be
manual or self-aware: the daemon evaluates risk and runtime confidence, then
either auto-approves low-risk work or parks tasks in a review queue.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask, TaskApproval

logger = get_logger(__name__)

_SENSITIVE_PATH_PREFIXES = (
    "backend/src/kortana/main.py",
    "backend/src/kortana/config.py",
    "backend/src/kortana/database.py",
    "backend/src/kortana/models.py",
    "backend/src/kortana/routers/auth",
    "backend/src/kortana/routers/billing",
    "backend/migrations",
    "docker-compose.yml",
    "Dockerfile",
    "backend/requirements",
    "package.json",
    ".env",
)


@dataclass
class ApprovalDecision:
    mode: str
    approved: bool
    review_required: bool
    reason_code: str
    rationale: str
    risk_score: int
    risk_level: str
    confidence: float
    file_count: int
    sensitive_paths: list[str] = field(default_factory=list)
    factors: list[str] = field(default_factory=list)
    validation_summary: dict[str, Any] = field(default_factory=dict)


class TaskApprovalService:
    """Assess and persist approval decisions for GitHub tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_task(
        self,
        task: GitHubTask,
        *,
        approval_mode: str | None,
        system_state: str,
        runtime_profile: dict[str, Any] | None,
        workspace_status: dict[str, Any] | None,
    ) -> ApprovalDecision | None:
        """Return an approval decision when approval mode is active."""
        mode = self._normalize_mode(approval_mode)
        if mode is None:
            return None

        confidence = self._runtime_confidence(runtime_profile)
        file_changes = self._extract_file_changes(task)
        file_count = len(file_changes)
        sensitive_paths = [
            path
            for path in file_changes
            if any(path.startswith(prefix) for prefix in _SENSITIVE_PATH_PREFIXES)
        ]
        validation_summary = self.summarize_validation(task)
        blocked_paths = list(validation_summary.get("blocked_paths") or [])
        failed_validations = list(validation_summary.get("failed_validations") or [])
        adjusted_validations = list(
            validation_summary.get("adjusted_validations") or []
        )
        planned_tests = list(validation_summary.get("planned_tests") or [])

        risk_score = 0
        factors: list[str] = []
        priority = (task.priority or "medium").lower()
        classification = (task.classification or "auto").lower()
        dirty_count = int((workspace_status or {}).get("changed_count") or 0)

        if classification in {"approval", "ho"}:
            risk_score += 4
            factors.append(f"classification:{classification}")
        if priority == "high":
            risk_score += 2
            factors.append("priority:high")
        elif priority == "medium":
            risk_score += 1
            factors.append("priority:medium")

        if file_count > 10:
            risk_score += 4
            factors.append("scope:very_large")
        elif file_count > 5:
            risk_score += 2
            factors.append("scope:large")
        elif file_count > 0:
            factors.append("scope:bounded")

        if sensitive_paths:
            risk_score += min(4, 2 + len(sensitive_paths))
            factors.append("sensitive_paths")
        if blocked_paths:
            risk_score += min(5, 3 + len(blocked_paths))
            factors.append("validation:blocked_paths")
        if failed_validations:
            risk_score += min(3, len(failed_validations))
            factors.append("validation:failed_checks")
        if adjusted_validations:
            risk_score += 1
            factors.append("validation:adjusted_plan")
        if (
            validation_summary.get("report_present")
            and file_count > 0
            and not planned_tests
        ):
            risk_score += 1
            factors.append("validation:no_tests")

        if system_state == "critical":
            risk_score += 6
            factors.append("system:critical")
        elif system_state == "degraded":
            risk_score += 3
            factors.append("system:degraded")
        elif system_state == "recovering":
            risk_score += 1
            factors.append("system:recovering")

        if dirty_count > 250:
            risk_score += 3
            factors.append("workspace:very_dirty")
        elif dirty_count > 50:
            risk_score += 1
            factors.append("workspace:dirty")

        min_confidence = float(os.getenv("SELF_AWARE_APPROVAL_MIN_CONFIDENCE", "0.68"))
        if confidence < min_confidence:
            risk_score += 2
            factors.append("confidence:low")

        if mode == "auto":
            approved = True
            review_required = False
            reason_code = "auto_approved"
        elif mode == "manual":
            approved = False
            review_required = True
            reason_code = "approval_required"
        else:
            approved = (
                system_state != "critical"
                and confidence >= min_confidence
                and risk_score <= int(os.getenv("SELF_AWARE_APPROVAL_MAX_RISK", "5"))
            )
            review_required = not approved
            reason_code = "self_approved" if approved else "self_approval_hold"

        risk_level = "low"
        if risk_score >= 7:
            risk_level = "high"
        elif risk_score >= 4:
            risk_level = "medium"

        rationale = self._build_rationale(
            mode=mode,
            approved=approved,
            confidence=confidence,
            risk_level=risk_level,
            factors=factors,
            sensitive_paths=sensitive_paths,
        )

        return ApprovalDecision(
            mode=mode,
            approved=approved,
            review_required=review_required,
            reason_code=reason_code,
            rationale=rationale,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            file_count=file_count,
            sensitive_paths=sensitive_paths,
            factors=factors,
            validation_summary=validation_summary,
        )

    async def record_decision(
        self,
        task: GitHubTask,
        decision: ApprovalDecision,
    ) -> TaskApproval:
        """Persist an approval decision and transition task state."""
        approval = await self._get_open_approval(task.id)
        if approval is None and decision.approved:
            approval = await self._get_latest_approval(task.id)
        if approval is None:
            approval = TaskApproval(
                github_task_id=str(task.id),
                approval_mode=decision.mode,
            )
            self.session.add(approval)

        approval.review_required = decision.review_required
        approval.rationale = decision.rationale
        approval.decision_factors = {
            "factors": decision.factors,
            "sensitive_paths": decision.sensitive_paths,
            "file_count": decision.file_count,
            "validation_summary": decision.validation_summary,
        }
        approval.risk_score = decision.risk_score
        approval.risk_level = decision.risk_level
        approval.confidence = decision.confidence
        approval.updated_at = datetime.utcnow()

        if decision.approved:
            approval.status = "auto_approved"
            approval.reviewer = (
                "autonomous" if decision.mode == "auto" else "self-aware"
            )
            approval.resolved_at = datetime.utcnow()
        else:
            approval.status = "pending"
            approval.reviewer = None
            approval.resolved_at = None
            task.status = "waiting_for_approval"

        await self.session.flush()
        return approval

    async def approve_task(
        self,
        task_id: str,
        *,
        approved: bool,
        reviewer: str,
        notes: str | None = None,
    ) -> GitHubTask:
        """Resolve a queued approval and transition the task."""
        task = await self._get_task(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.status not in {"waiting_for_approval", "waiting_for_ho"}:
            raise ValueError(f"Task is not awaiting approval (status: {task.status})")

        approval = await self._get_open_approval(task_id)
        if approval is None:
            approval = TaskApproval(
                github_task_id=task_id,
                approval_mode="manual",
                status="pending",
                review_required=True,
            )
            self.session.add(approval)

        approval.status = "approved" if approved else "rejected"
        approval.reviewer = reviewer
        approval.notes = notes
        approval.resolved_at = datetime.utcnow()
        approval.updated_at = datetime.utcnow()

        if approved:
            task.status = "planning_complete"
            task.classification = "auto"
        else:
            task.status = "cancelled"
        await self.session.flush()
        return task

    async def list_pending(self, limit: int = 20) -> list[TaskApproval]:
        stmt = (
            select(TaskApproval)
            .where(TaskApproval.status == "pending")
            .order_by(TaskApproval.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def serialize(approval: TaskApproval) -> dict[str, Any]:
        decision_factors = approval.decision_factors or {}
        return {
            "id": approval.id,
            "github_task_id": approval.github_task_id,
            "status": approval.status,
            "approval_mode": approval.approval_mode,
            "review_required": approval.review_required,
            "reviewer": approval.reviewer,
            "rationale": approval.rationale,
            "decision_factors": decision_factors,
            "validation_summary": decision_factors.get("validation_summary") or {},
            "risk_score": approval.risk_score,
            "risk_level": approval.risk_level,
            "confidence": approval.confidence,
            "notes": approval.notes,
            "created_at": approval.created_at.isoformat()
            if approval.created_at
            else None,
            "updated_at": approval.updated_at.isoformat()
            if approval.updated_at
            else None,
            "resolved_at": approval.resolved_at.isoformat()
            if approval.resolved_at
            else None,
        }

    @staticmethod
    def summarize_validation(task: GitHubTask | None) -> dict[str, Any]:
        report = getattr(task, "validation_report", None)
        if not isinstance(report, dict):
            return {
                "report_present": False,
                "stage": None,
                "blocked_paths": [],
                "planned_tests": [],
                "changed_files": [],
                "validation_notes": [],
                "failed_validations": [],
                "adjusted_validations": [],
                "history_length": 0,
            }

        blocked_paths = TaskApprovalService._normalized_strings(
            report.get("blocked_paths")
        )
        planned_tests = TaskApprovalService._normalized_strings(
            report.get("planned_tests")
        )
        changed_files = TaskApprovalService._normalized_strings(
            report.get("changed_files") or report.get("planned_files")
        )
        validation_notes = TaskApprovalService._normalized_strings(
            report.get("validation_notes")
        )

        failed_validations: list[str] = []
        adjusted_validations: list[str] = []
        validations = report.get("validations")
        if isinstance(validations, list):
            for item in validations:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name") or "unknown").strip()
                status = str(item.get("status") or "unknown").strip().lower()
                if status in {"blocked", "failed"}:
                    failed_validations.append(name)
                elif status == "adjusted":
                    adjusted_validations.append(name)

        history = report.get("history")
        history_length = len(history) if isinstance(history, list) else 0

        return {
            "report_present": True,
            "stage": report.get("stage"),
            "blocked_paths": blocked_paths,
            "planned_tests": planned_tests,
            "changed_files": changed_files,
            "validation_notes": validation_notes,
            "failed_validations": failed_validations,
            "adjusted_validations": adjusted_validations,
            "history_length": history_length,
        }

    async def _get_open_approval(self, task_id: str) -> TaskApproval | None:
        stmt = (
            select(TaskApproval)
            .where(
                TaskApproval.github_task_id == str(task_id),
                TaskApproval.status == "pending",
            )
            .order_by(TaskApproval.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_latest_approval(self, task_id: str) -> TaskApproval | None:
        stmt = (
            select(TaskApproval)
            .where(TaskApproval.github_task_id == str(task_id))
            .order_by(TaskApproval.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_task(self, task_id: str) -> GitHubTask | None:
        stmt = select(GitHubTask).where(GitHubTask.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _normalize_mode(approval_mode: str | None) -> str | None:
        if approval_mode is None:
            default_mode = (
                (os.getenv("KORTANA_DEFAULT_APPROVAL_MODE") or "").strip().lower()
            )
            if default_mode in {"auto", "manual", "self-aware", "none"}:
                if default_mode == "none":
                    return None
                return default_mode
            if os.getenv("KORTANA_SELF_AWARE_APPROVAL", "false").lower() == "true":
                return "self-aware"
            return None

        lowered = approval_mode.strip().lower()
        if lowered in {"manual", "auto", "self-aware", "self aware", "autonomous"}:
            if lowered in {"self aware", "autonomous"}:
                return "self-aware"
            return lowered
        return None

    @staticmethod
    def _runtime_confidence(runtime_profile: dict[str, Any] | None) -> float:
        if not runtime_profile:
            return 0.5
        raw = runtime_profile.get("execution_confidence", 0.5)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.5

    @staticmethod
    def _extract_file_changes(task: GitHubTask) -> list[str]:
        plan_text = task.plan or ""
        try:
            payload = json.loads(plan_text)
        except json.JSONDecodeError:
            return []

        files = payload.get("FILE_CHANGES") or payload.get("files") or []
        changed: list[str] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            candidate = str(item.get("file") or item.get("path") or "").strip()
            if candidate and candidate not in changed:
                changed.append(candidate.replace("\\", "/"))
        return changed

    @staticmethod
    def _build_rationale(
        *,
        mode: str,
        approved: bool,
        confidence: float,
        risk_level: str,
        factors: list[str],
        sensitive_paths: list[str],
    ) -> str:
        verb = "auto-approved" if approved else "held for review"
        factor_text = ", ".join(factors[:6]) if factors else "no major risk factors"
        sensitive_text = ""
        if sensitive_paths:
            sensitive_text = f" Sensitive paths: {', '.join(sensitive_paths[:4])}."
        return (
            f"{mode} approval {verb} with confidence {confidence:.2f} "
            f"and {risk_level} risk. Factors: {factor_text}.{sensitive_text}"
        )

    @staticmethod
    def _normalized_strings(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        normalized: list[str] = []
        for item in value:
            candidate = str(item).strip()
            if candidate and candidate not in normalized:
                normalized.append(candidate)
        return normalized
