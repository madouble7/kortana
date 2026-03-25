"""
KOR'TANA Self-Diagnostic Loop — Phase 8 Cycle #2: Self-Repair
Gemini-powered failure analysis → root cause → auto-fix attempt → pattern storage.
"""

import logging
import os
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import AuditLog

logger = logging.getLogger(__name__)

ANALYSIS_MODEL = "gemini-2.0-flash"


class DiagnosticResult:
    """Result of a self-diagnostic analysis."""

    __slots__ = (
        "id",
        "timestamp",
        "error_type",
        "error_message",
        "root_cause",
        "suggested_fix",
        "confidence",
        "auto_fixable",
        "context",
    )

    def __init__(
        self,
        error_type: str,
        error_message: str,
        root_cause: str = "",
        suggested_fix: str = "",
        confidence: float = 0.0,
        auto_fixable: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.error_type = error_type
        self.error_message = error_message
        self.root_cause = root_cause
        self.suggested_fix = suggested_fix
        self.confidence = confidence
        self.auto_fixable = auto_fixable
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "root_cause": self.root_cause,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
            "auto_fixable": self.auto_fixable,
        }


async def _call_gemini_analysis(prompt: str) -> Optional[str]:
    """Call Gemini to analyze an error and return root cause analysis."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Gemini API key — diagnostic analysis skipped")
        return None
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=ANALYSIS_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini diagnostic call failed: {e}")
        return None


class SelfDiagnostic:
    """Autonomous failure analysis and self-repair engine."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._history: List[DiagnosticResult] = []
        self._pattern_cache: Dict[str, DiagnosticResult] = {}

    # ------------------------------------------------------------------
    # Analyze a failure
    # ------------------------------------------------------------------
    async def analyze_failure(
        self,
        error: Exception,
        task_context: Optional[Dict[str, Any]] = None,
    ) -> DiagnosticResult:
        """Analyze an exception using Gemini for root cause + fix suggestion."""
        error_type = type(error).__name__
        error_message = str(error)
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb_str = "".join(tb[-5:])  # Last 5 frames max

        # Check pattern cache first
        cache_key = f"{error_type}:{error_message[:100]}"
        if cache_key in self._pattern_cache:
            cached = self._pattern_cache[cache_key]
            logger.info(f"Diagnostic cache hit for {error_type}")
            return cached

        prompt = (
            "You are KOR'TANA's self-diagnostic engine. Analyze this failure and "
            "provide a concise root cause + fix.\n\n"
            f"Error Type: {error_type}\n"
            f"Error Message: {error_message}\n"
            f"Traceback (last 5 frames):\n{tb_str}\n"
        )
        if task_context:
            ctx_str = "\n".join(f"  {k}: {v}" for k, v in task_context.items())
            prompt += f"\nTask Context:\n{ctx_str}\n"

        prompt += (
            "\nRespond in this exact format:\n"
            "ROOT_CAUSE: <one-line root cause>\n"
            "SUGGESTED_FIX: <one-line fix>\n"
            "CONFIDENCE: <0.0-1.0>\n"
            "AUTO_FIXABLE: <true/false>\n"
        )

        analysis = await _call_gemini_analysis(prompt)

        root_cause = ""
        suggested_fix = ""
        confidence = 0.0
        auto_fixable = False

        if analysis:
            for line in analysis.strip().split("\n"):
                line = line.strip()
                if line.startswith("ROOT_CAUSE:"):
                    root_cause = line[len("ROOT_CAUSE:") :].strip()
                elif line.startswith("SUGGESTED_FIX:"):
                    suggested_fix = line[len("SUGGESTED_FIX:") :].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line[len("CONFIDENCE:") :].strip())
                    except ValueError:
                        confidence = 0.5
                elif line.startswith("AUTO_FIXABLE:"):
                    auto_fixable = (
                        line[len("AUTO_FIXABLE:") :].strip().lower() == "true"
                    )

        result = DiagnosticResult(
            error_type=error_type,
            error_message=error_message,
            root_cause=root_cause or f"Unresolved {error_type}",
            suggested_fix=suggested_fix or "Manual investigation required",
            confidence=confidence,
            auto_fixable=auto_fixable,
            context=task_context,
        )

        # Cache and record
        self._pattern_cache[cache_key] = result
        self._history.append(result)

        # Persist to audit log
        await self._persist_diagnostic(result)

        logger.info(
            f"Diagnostic: {error_type} → {root_cause} "
            f"(confidence={confidence:.2f}, auto_fixable={auto_fixable})"
        )
        return result

    # ------------------------------------------------------------------
    # Analyze from string (for API calls without an exception object)
    # ------------------------------------------------------------------
    async def analyze_error_string(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DiagnosticResult:
        """Analyze an error described by strings (no exception object)."""
        cache_key = f"{error_type}:{error_message[:100]}"
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        prompt = (
            "You are KOR'TANA's self-diagnostic engine. Analyze this failure:\n\n"
            f"Error Type: {error_type}\n"
            f"Error Message: {error_message}\n"
        )
        if context:
            ctx_str = "\n".join(f"  {k}: {v}" for k, v in context.items())
            prompt += f"\nContext:\n{ctx_str}\n"

        prompt += (
            "\nRespond in this exact format:\n"
            "ROOT_CAUSE: <one-line root cause>\n"
            "SUGGESTED_FIX: <one-line fix>\n"
            "CONFIDENCE: <0.0-1.0>\n"
            "AUTO_FIXABLE: <true/false>\n"
        )

        analysis = await _call_gemini_analysis(prompt)

        root_cause = ""
        suggested_fix = ""
        confidence = 0.0
        auto_fixable = False

        if analysis:
            for line in analysis.strip().split("\n"):
                line = line.strip()
                if line.startswith("ROOT_CAUSE:"):
                    root_cause = line[len("ROOT_CAUSE:") :].strip()
                elif line.startswith("SUGGESTED_FIX:"):
                    suggested_fix = line[len("SUGGESTED_FIX:") :].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line[len("CONFIDENCE:") :].strip())
                    except ValueError:
                        confidence = 0.5
                elif line.startswith("AUTO_FIXABLE:"):
                    auto_fixable = (
                        line[len("AUTO_FIXABLE:") :].strip().lower() == "true"
                    )

        result = DiagnosticResult(
            error_type=error_type,
            error_message=error_message,
            root_cause=root_cause or f"Unresolved {error_type}",
            suggested_fix=suggested_fix or "Manual investigation required",
            confidence=confidence,
            auto_fixable=auto_fixable,
            context=context,
        )

        self._pattern_cache[cache_key] = result
        self._history.append(result)
        await self._persist_diagnostic(result)
        return result

    # ------------------------------------------------------------------
    # History & patterns
    # ------------------------------------------------------------------
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent diagnostic history."""
        return [d.to_dict() for d in self._history[-limit:]]

    def get_known_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Return all cached failure patterns."""
        return {k: v.to_dict() for k, v in self._pattern_cache.items()}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    async def _persist_diagnostic(self, result: DiagnosticResult) -> None:
        """Store diagnostic result in the audit log."""
        log_entry = AuditLog(
            action="self_diagnostic",
            resource_type="diagnostic",
            resource_id=result.id,
            details={
                "error_type": result.error_type,
                "error_message": result.error_message[:500],
                "root_cause": result.root_cause,
                "suggested_fix": result.suggested_fix,
                "confidence": result.confidence,
                "auto_fixable": result.auto_fixable,
            },
        )
        self.db.add(log_entry)
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to persist diagnostic: {e}")
            await self.db.rollback()

    # ------------------------------------------------------------------
    # Load history from DB on startup
    # ------------------------------------------------------------------
    async def load_history(self, limit: int = 50) -> None:
        """Load recent diagnostic history from audit log into memory."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == "self_diagnostic")
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        for log_entry in reversed(logs):
            details = log_entry.details or {}
            dr = DiagnosticResult(
                error_type=details.get("error_type", "unknown"),
                error_message=details.get("error_message", ""),
                root_cause=details.get("root_cause", ""),
                suggested_fix=details.get("suggested_fix", ""),
                confidence=details.get("confidence", 0.0),
                auto_fixable=details.get("auto_fixable", False),
            )
            self._history.append(dr)
            cache_key = f"{dr.error_type}:{dr.error_message[:100]}"
            self._pattern_cache[cache_key] = dr

        logger.info(f"Loaded {len(logs)} diagnostic records from history")
