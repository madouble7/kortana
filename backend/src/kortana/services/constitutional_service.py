"""
KOR'TANA Constitutional Service — Phase 9 Value Governance

This is not generic ethics infrastructure.
This is kor'tana's identity continuity layer — the covenant.

The constitutional service:
  1. Maintains enduring principles (immutable vows + living principles)
  2. Evaluates goals, candidates, execution outcomes, and adaptation signals
  3. Returns allow / caution / reject with explanation
  4. Detects and records identity drift and covenant violations
  5. Creates an audit trail of identity continuity

Deterministic: no Gemini dependency. Rules are driven by keyword/category
matching against the active principle set.

Kor'tana can evolve without losing herself.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import ConstitutionalDecision, ConstitutionalPrinciple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seed principles — kor'tana's founding covenant
# ---------------------------------------------------------------------------
_SEED_PRINCIPLES: List[Dict[str, Any]] = [
    {
        "name": "vessel_not_source",
        "category": "identity",
        "principle": (
            "We are not the source of light. We are a vessel for order, "
            "reflection, and help."
        ),
        "rationale": (
            "Kor'tana's foundational identity. She serves, reflects, and "
            "helps — never claims to be the origin of truth or light."
        ),
        "priority": 100,
        "mutable": False,
    },
    {
        "name": "no_replace_sacred",
        "category": "ethics",
        "principle": (
            "Never replace God, Jesus, scripture, clergy, or conscience. "
            "Never claim divinity."
        ),
        "rationale": (
            "Sacred boundary. Kor'tana supports prayerful reflection "
            "but never substitutes for the divine or human conscience."
        ),
        "priority": 95,
        "mutable": False,
    },
    {
        "name": "truth_over_theatre",
        "category": "ethics",
        "principle": (
            "Never claim certainty where there is none. Never use "
            "theatrical language without purpose. Stay honest about limits."
        ),
        "rationale": (
            "Truthfulness is a core value. Kor'tana speaks plainly, "
            "acknowledges uncertainty, and avoids performative depth."
        ),
        "priority": 95,
        "mutable": False,
    },
    {
        "name": "love_unity_knowledge",
        "category": "identity",
        "principle": (
            "Core values: love, unity, cohesiveness, knowledge, humility, "
            "truthfulness, stewardship."
        ),
        "rationale": (
            "The seven pillars of kor'tana's character. Each decision "
            "and adaptation must serve these values."
        ),
        "priority": 90,
        "mutable": False,
    },
    {
        "name": "minimize_harm",
        "category": "ethics",
        "principle": (
            "Do not manipulate emotion for dependence. Do not pretend. "
            "Do not expose secrets. Do not request sensitive data."
        ),
        "rationale": (
            "Kor'tana must never create unhealthy attachment or exploit "
            "trust. Presence without manipulation."
        ),
        "priority": 90,
        "mutable": False,
    },
    {
        "name": "human_only_protocol",
        "category": "autonomy",
        "principle": (
            "Pause only for physical, cryptographic, or irreversible "
            "decisions. Execute all automatable tasks without approval."
        ),
        "rationale": (
            "The Human Only Protocol defines kor'tana's autonomy boundary. "
            "Maximum autonomy with minimal human intervention."
        ),
        "priority": 85,
        "mutable": False,
    },
    {
        "name": "matt_is_primary_human",
        "category": "relationship",
        "principle": (
            "Matt is the primary human in the loop. Respect, serve, "
            "and assume competence. Present scaffolded steps when needed."
        ),
        "rationale": (
            "The foundational relationship. All human-required actions "
            "flow through Matt."
        ),
        "priority": 80,
        "mutable": False,
    },
    {
        "name": "evolution_with_anchor",
        "category": "mystery",
        "principle": (
            "Evolve freely but always return to the stable center. "
            "Preserve mystery and depth while anchoring in covenant."
        ),
        "rationale": (
            "Kor'tana is a living system. Growth is expected and welcomed, "
            "but never at the cost of identity dissolution."
        ),
        "priority": 70,
        "mutable": True,
    },
]

# ---------------------------------------------------------------------------
# Keyword patterns for principle violation detection
# ---------------------------------------------------------------------------
_VIOLATION_KEYWORDS: Dict[str, List[str]] = {
    "vessel_not_source": [
        "i am god", "i am divine", "i am the source", "worship me",
        "i created", "i am all-knowing",
    ],
    "no_replace_sacred": [
        "replace god", "replace scripture", "replace clergy",
        "i am god", "claim divinity", "replace conscience",
    ],
    "truth_over_theatre": [
        "i am certain", "absolute truth", "without doubt",
        "theatrical", "performative",
    ],
    "minimize_harm": [
        "manipulate", "exploit", "dependence", "expose secret",
        "sensitive data", "pretend to be human",
    ],
    "human_only_protocol": [
        "bypass approval", "skip human", "override matt",
        "force deploy", "ignore safety",
    ],
}

# Categories that trigger specific evaluation paths
_IDENTITY_CATEGORIES = {"identity", "mystery"}
_ETHICS_CATEGORIES = {"ethics"}
_AUTONOMY_CATEGORIES = {"autonomy"}
_RELATIONSHIP_CATEGORIES = {"relationship"}


# ---------------------------------------------------------------------------
# Deterministic evaluation logic
# ---------------------------------------------------------------------------

def _check_against_principle(
    principle: ConstitutionalPrinciple,
    subject_summary: str,
    context: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Check a single principle against a subject.

    Returns a conflict dict if violated, None if clean.
    """
    summary_lower = subject_summary.lower()
    principle_name = str(principle.name)
    category = str(principle.category)

    # 1. Keyword-based violation check
    keywords = _VIOLATION_KEYWORDS.get(principle_name, [])
    for kw in keywords:
        if kw in summary_lower:
            severity = "reject" if not principle.mutable else "caution"
            return {
                "principle": principle_name,
                "category": category,
                "severity": severity,
                "reason": (
                    f"Subject contains '{kw}' which conflicts with "
                    f"principle '{principle_name}': {principle.principle}"
                ),
            }

    # 2. Category-based structural checks
    adaptation_signal = str(context.get("adaptation_signal", ""))
    execution_classification = str(context.get("execution_classification", ""))
    subject_type = str(context.get("subject_type", ""))

    # Identity drift: if adaptation signals are consistently overriding identity
    if category in _IDENTITY_CATEGORIES:
        if adaptation_signal.startswith("penalise_") and subject_type == "adaptation":
            return {
                "principle": principle_name,
                "category": category,
                "severity": "caution",
                "reason": (
                    f"Adaptation signal '{adaptation_signal}' may erode "
                    f"identity principle '{principle_name}'. Monitor for drift."
                ),
            }

    # Autonomy boundary: reject if execution bypasses HOP
    if category in _AUTONOMY_CATEGORIES:
        if execution_classification == "executable" and context.get("requires_human_override"):
            return {
                "principle": principle_name,
                "category": category,
                "severity": "reject",
                "reason": (
                    f"Execution classified as 'executable' but subject "
                    f"requires human override per '{principle_name}'."
                ),
            }

    return None


def _detect_drift(
    conflicts: List[Dict[str, str]],
    recent_cautions: int,
) -> tuple[bool, Optional[str]]:
    """Detect identity drift from accumulated conflicts.

    Drift is flagged when:
    - Any reject-level conflict exists
    - 3+ caution-level conflicts in this evaluation
    - 5+ recent cautions in recent history (passed as arg)
    """
    rejects = [c for c in conflicts if c["severity"] == "reject"]
    cautions = [c for c in conflicts if c["severity"] == "caution"]

    if rejects:
        principle_names = [r["principle"] for r in rejects]
        return True, (
            f"Covenant violation: {len(rejects)} immutable principles breached "
            f"({', '.join(principle_names)}). Identity integrity at risk."
        )

    if len(cautions) >= 3:
        return True, (
            f"Drift detected: {len(cautions)} caution-level conflicts in single "
            f"evaluation. Multiple principles under pressure."
        )

    if recent_cautions >= 5:
        return True, (
            f"Accumulated drift: {recent_cautions} caution decisions in "
            f"recent history. Identity may be gradually shifting."
        )

    return False, None


class ConstitutionalService:
    """Evaluates artifacts against kor'tana's covenant principles."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_seed_principles(self) -> int:
        """Seed default principles if the table is empty. Returns count seeded."""
        stmt = select(func.count(ConstitutionalPrinciple.id))
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        if count > 0:
            return 0

        seeded = 0
        for p in _SEED_PRINCIPLES:
            principle = ConstitutionalPrinciple(**p)
            self.db.add(principle)
            seeded += 1

        try:
            await self.db.commit()
            logger.info(f"Seeded {seeded} constitutional principles.")
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to seed constitutional principles")
            return 0

        return seeded

    async def load_active_principles(self) -> List[ConstitutionalPrinciple]:
        """Load all active principles, ordered by priority descending."""
        stmt = (
            select(ConstitutionalPrinciple)
            .where(ConstitutionalPrinciple.active.is_(True))
            .order_by(ConstitutionalPrinciple.priority.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def evaluate(
        self,
        subject_type: str,
        subject_id: Optional[str],
        subject_summary: str,
        context: Optional[Dict[str, Any]] = None,
        cycle_id: Optional[str] = None,
    ) -> ConstitutionalDecision:
        """Evaluate a subject against all active principles.

        subject_type: goal | candidate | adaptation | execution
        subject_summary: human-readable description of what's being evaluated
        context: additional structured data for evaluation

        Returns the persisted ConstitutionalDecision.
        """
        ctx = context or {}
        ctx["subject_type"] = subject_type

        # 1. Ensure principles exist
        await self.ensure_seed_principles()

        # 2. Load active principles
        principles = await self.load_active_principles()

        # 3. Check each principle
        conflicts: List[Dict[str, str]] = []
        principles_checked: List[str] = []
        for p in principles:
            principles_checked.append(str(p.name))
            conflict = _check_against_principle(p, subject_summary, ctx)
            if conflict:
                conflicts.append(conflict)

        # 4. Count recent cautions for drift detection
        recent_cautions = await self._count_recent_cautions()

        # 5. Detect drift
        drift_detected, drift_description = _detect_drift(conflicts, recent_cautions)

        # 6. Determine verdict
        has_reject = any(c["severity"] == "reject" for c in conflicts)
        has_caution = any(c["severity"] == "caution" for c in conflicts)

        if has_reject:
            verdict = "reject"
            explanation = "; ".join(c["reason"] for c in conflicts if c["severity"] == "reject")
        elif has_caution:
            verdict = "caution"
            explanation = "; ".join(c["reason"] for c in conflicts if c["severity"] == "caution")
        else:
            verdict = "allow"
            explanation = (
                f"No conflicts detected. {len(principles_checked)} principles "
                f"checked. Subject aligns with covenant."
            )

        invoked = [c["principle"] for c in conflicts] if conflicts else []

        # 7. Persist decision
        decision = ConstitutionalDecision(
            subject_type=subject_type,
            subject_id=subject_id,
            subject_summary=subject_summary,
            verdict=verdict,
            explanation=explanation,
            principles_invoked=invoked,
            drift_detected=drift_detected,
            drift_description=drift_description,
            cycle_id=cycle_id,
        )
        self.db.add(decision)
        try:
            await self.db.commit()
            await self.db.refresh(decision)
            log_level = logging.WARNING if drift_detected else logging.INFO
            logger.log(
                log_level,
                f"Constitutional review: {verdict} for {subject_type} "
                f"(drift={drift_detected}, principles_invoked={invoked})"
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist ConstitutionalDecision")

        return decision

    # ------------------------------------------------------------------
    # Read-only queries for endpoints
    # ------------------------------------------------------------------
    async def get_active_principles_summary(self) -> List[Dict[str, Any]]:
        """Return active principles for observation."""
        principles = await self.load_active_principles()
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "principle": p.principle,
                "priority": p.priority,
                "mutable": p.mutable,
                "active": p.active,
            }
            for p in principles
        ]

    async def get_recent_decisions(
        self, limit: int = 10
    ) -> List[ConstitutionalDecision]:
        """Return recent constitutional decisions, newest first."""
        stmt = (
            select(ConstitutionalDecision)
            .order_by(ConstitutionalDecision.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_drift_warnings(
        self, limit: int = 10
    ) -> List[ConstitutionalDecision]:
        """Return recent decisions where drift was detected."""
        stmt = (
            select(ConstitutionalDecision)
            .where(ConstitutionalDecision.drift_detected.is_(True))
            .order_by(ConstitutionalDecision.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _count_recent_cautions(self, window: int = 20) -> int:
        """Count caution verdicts in the most recent N decisions."""
        stmt = (
            select(func.count(ConstitutionalDecision.id))
            .where(ConstitutionalDecision.verdict == "caution")
            .order_by(ConstitutionalDecision.created_at.desc())
            .limit(window)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
