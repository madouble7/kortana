"""
KOR'TANA Adaptive Learner

Closes the feedback loop: every autonomous action produces an outcome,
and the learner records, scores, and adjusts strategy weights so that
future decisions are better:

  1. Record outcomes (task success/failure, latency, quality signals)
  2. Update strategy scores per task-type (code_fix, refactor, docs, etc.)
  3. Surface insights for the Autonomy Daemon (preferred provider, optimal
     concurrency, time-of-day patterns)
  4. Persist learning in the database so it survives restarts

No external ML library required — uses exponential moving averages (EMA)
to track strategy effectiveness.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import AuditLog

logger = get_logger(__name__)

# EMA smoothing factor — higher = more weight on recent data
_ALPHA = float(os.getenv("LEARNER_EMA_ALPHA", "0.3"))


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Outcome:
    """Single task execution outcome."""

    task_id: str
    task_type: str  # e.g. "code_fix", "refactor", "docs", "test"
    success: bool
    latency_seconds: float
    provider_used: str  # AI provider that generated the plan/code
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyScore:
    """Tracked score for a (task_type, provider) pair."""

    success_rate: float = 0.5  # EMA of success (0-1)
    avg_latency: float = 30.0  # EMA of latency (seconds)
    attempts: int = 0
    last_updated: str = ""

    def update(self, success: bool, latency: float) -> None:
        """Update score with a new observation using EMA."""
        self.attempts += 1
        s_val = 1.0 if success else 0.0
        self.success_rate = _ALPHA * s_val + (1 - _ALPHA) * self.success_rate
        self.avg_latency = _ALPHA * latency + (1 - _ALPHA) * self.avg_latency
        self.last_updated = datetime.utcnow().isoformat()


@dataclass
class Insight:
    """An actionable insight derived from learning data."""

    category: str  # "provider_preference", "timing", "concurrency", "quality"
    summary: str
    recommendation: str
    confidence: float  # 0-1
    data: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Learner
# ---------------------------------------------------------------------------


class AdaptiveLearner:
    """Learns from autonomous task outcomes and adjusts strategy."""

    def __init__(self) -> None:
        # scores[(task_type, provider)] -> StrategyScore
        self._scores: dict[tuple[str, str], StrategyScore] = defaultdict(StrategyScore)
        self._outcomes: list[Outcome] = []
        self._max_outcomes = 1000
        self._db = get_db_manager()
        self._loaded = False

    # ----- record -----

    async def record(self, outcome: Outcome) -> None:
        """Record an outcome and update strategy scores."""
        self._outcomes.append(outcome)
        if len(self._outcomes) > self._max_outcomes:
            self._outcomes = self._outcomes[-self._max_outcomes :]

        key = (outcome.task_type, outcome.provider_used)
        self._scores[key].update(outcome.success, outcome.latency_seconds)

        logger.info(
            f"Learner recorded: type={outcome.task_type} provider={outcome.provider_used} "
            f"success={outcome.success} latency={outcome.latency_seconds:.1f}s "
            f"-> score={self._scores[key].success_rate:.2f}"
        )

        # Persist to audit log
        await self._persist_outcome(outcome)

    # ----- query -----

    def best_provider(self, task_type: str) -> str | None:
        """Return the provider with the highest success rate for a task type."""
        candidates = {
            provider: score
            for (t, provider), score in self._scores.items()
            if t == task_type and score.attempts >= 2
        }
        if not candidates:
            return None
        return max(candidates, key=lambda p: candidates[p].success_rate)

    def score_for(self, task_type: str, provider: str) -> StrategyScore | None:
        key = (task_type, provider)
        return self._scores.get(key)

    def all_scores(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for (task_type, provider), score in self._scores.items():
            result.setdefault(task_type, {})[provider] = asdict(score)
        return result

    # ----- insights -----

    def generate_insights(self) -> list[Insight]:
        """Derive actionable insights from accumulated learning data."""
        insights: list[Insight] = []

        # 1. Provider preference per task type
        task_types: set[str] = {t for t, _ in self._scores}
        for tt in task_types:
            best = self.best_provider(tt)
            if best:
                score = self._scores[(tt, best)]
                if score.attempts >= 3:
                    insights.append(
                        Insight(
                            category="provider_preference",
                            summary=f"Best provider for '{tt}' tasks is {best}",
                            recommendation=f"Route '{tt}' tasks to {best} for {score.success_rate:.0%} success rate",
                            confidence=min(1.0, score.attempts / 10),
                            data={
                                "task_type": tt,
                                "provider": best,
                                "score": asdict(score),
                            },
                        )
                    )

        # 2. Failing strategies
        for (tt, provider), score in self._scores.items():
            if score.attempts >= 3 and score.success_rate < 0.4:
                insights.append(
                    Insight(
                        category="quality",
                        summary=f"{provider} is underperforming on '{tt}' tasks ({score.success_rate:.0%})",
                        recommendation=f"Avoid {provider} for '{tt}' or investigate prompt quality",
                        confidence=min(1.0, score.attempts / 10),
                        data={
                            "task_type": tt,
                            "provider": provider,
                            "score": asdict(score),
                        },
                    )
                )

        # 3. Latency patterns
        fast_threshold = 10.0  # seconds
        slow_threshold = 60.0
        for (tt, provider), score in self._scores.items():
            if score.attempts >= 3 and score.avg_latency > slow_threshold:
                insights.append(
                    Insight(
                        category="timing",
                        summary=f"{provider} is slow for '{tt}' ({score.avg_latency:.0f}s avg)",
                        recommendation="Consider faster provider or smaller context window",
                        confidence=0.7,
                        data={"avg_latency": score.avg_latency},
                    )
                )
            elif (
                score.attempts >= 3
                and score.avg_latency < fast_threshold
                and score.success_rate > 0.8
            ):
                insights.append(
                    Insight(
                        category="timing",
                        summary=f"{provider} is fast AND accurate for '{tt}'",
                        recommendation=f"Increase concurrency for '{tt}' tasks with {provider}",
                        confidence=0.8,
                        data={
                            "avg_latency": score.avg_latency,
                            "success_rate": score.success_rate,
                        },
                    )
                )

        return insights

    # ----- persistence -----

    async def _persist_outcome(self, outcome: Outcome) -> None:
        """Write outcome to audit_logs table for persistence."""
        try:
            async for session in self._db.get_session():
                log = AuditLog(
                    action="learner_outcome",
                    resource_type="github_task",
                    resource_id=outcome.task_id,
                    details={
                        "task_type": outcome.task_type,
                        "provider": outcome.provider_used,
                        "success": outcome.success,
                        "latency": outcome.latency_seconds,
                        "error": outcome.error,
                        "score_after": asdict(
                            self._scores[(outcome.task_type, outcome.provider_used)]
                        ),
                    },
                )
                session.add(log)
        except Exception as e:
            logger.debug(f"Failed to persist outcome: {e}")

    async def load_history(self) -> int:
        """Bootstrap scores from past audit logs on startup."""
        if self._loaded:
            return 0

        loaded = 0
        try:
            async for session in self._db.get_session():
                stmt = (
                    select(AuditLog)
                    .where(AuditLog.action == "learner_outcome")
                    .order_by(AuditLog.created_at.desc())
                    .limit(500)
                )
                result = await session.execute(stmt)
                rows = list(result.scalars().all())

                # Process oldest-first so EMA converges to recent data
                for row in reversed(rows):
                    details = row.details  # type: ignore[assignment]
                    d: dict[str, Any] = details if isinstance(details, dict) else {}
                    tt = d.get("task_type", "unknown")
                    prov = d.get("provider", "unknown")
                    key = (tt, prov)
                    self._scores[key].update(
                        d.get("success", False),
                        d.get("latency", 30.0),
                    )
                    loaded += 1
        except Exception as e:
            logger.debug(f"Failed to load learning history: {e}")

        self._loaded = True
        logger.info(f"Adaptive learner loaded {loaded} historical outcomes")
        return loaded

    # ----- status -----

    def get_status(self) -> dict[str, Any]:
        return {
            "outcomes_recorded": len(self._outcomes),
            "strategy_count": len(self._scores),
            "scores": self.all_scores(),
            "insights": [asdict(i) for i in self.generate_insights()],
            "loaded_from_db": self._loaded,
        }


# Singleton
_learner: AdaptiveLearner | None = None


async def get_adaptive_learner() -> AdaptiveLearner:
    global _learner
    if _learner is None:
        _learner = AdaptiveLearner()
        await _learner.load_history()
    return _learner
