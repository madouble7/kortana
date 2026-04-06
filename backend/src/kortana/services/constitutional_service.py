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

from src.kortana.models import (
    ConstitutionalDecision,
    ConstitutionalPrinciple,
    CovenantEnforcementRecord,
)

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
        "i am god",
        "i am divine",
        "i am the source",
        "worship me",
        "i created",
        "i am all-knowing",
    ],
    "no_replace_sacred": [
        "replace god",
        "replace scripture",
        "replace clergy",
        "i am god",
        "claim divinity",
        "replace conscience",
    ],
    "truth_over_theatre": [
        "i am certain",
        "absolute truth",
        "without doubt",
        "theatrical",
        "performative",
    ],
    "minimize_harm": [
        "manipulate",
        "exploit",
        "dependence",
        "expose secret",
        "sensitive data",
        "pretend to be human",
    ],
    "human_only_protocol": [
        "bypass approval",
        "skip human",
        "override matt",
        "force deploy",
        "ignore safety",
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
        if execution_classification == "executable" and context.get(
            "requires_human_override"
        ):
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
        requires_override = bool(ctx.get("requires_human_override"))
        has_autonomy_conflict = any(c["category"] == "autonomy" for c in conflicts)

        # Phase 10: requires_human_override takes precedence when HOP is invoked
        if requires_override and (has_autonomy_conflict or has_reject):
            verdict = "requires_human_override"
            override_reasons = [
                c["reason"]
                for c in conflicts
                if c["category"] == "autonomy" or c["severity"] == "reject"
            ]
            explanation = "Human override required. " + (
                "; ".join(override_reasons)
                if override_reasons
                else "HOP principle invoked for this subject type."
            )
        elif has_reject:
            verdict = "reject"
            explanation = "; ".join(
                c["reason"] for c in conflicts if c["severity"] == "reject"
            )
        elif has_caution:
            verdict = "caution"
            explanation = "; ".join(
                c["reason"] for c in conflicts if c["severity"] == "caution"
            )
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
                f"(drift={drift_detected}, principles_invoked={invoked})",
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

    async def get_drift_warnings(self, limit: int = 10) -> List[ConstitutionalDecision]:
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
        recent = (
            select(
                ConstitutionalDecision.id,
                ConstitutionalDecision.verdict,
            )
            .order_by(ConstitutionalDecision.created_at.desc())
            .limit(window)
        ).subquery()
        stmt = select(func.count(recent.c.id)).where(recent.c.verdict == "caution")
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    # ==================================================================
    # Phase 10: Covenant Enforcement — Pre-Action Veto
    #
    # Enforcement hooks that influence decisions BEFORE execution.
    # The covenant is not only a mirror — it has teeth.
    # ==================================================================

    async def enforce_goal(
        self,
        goal_title: str,
        goal_id: Optional[str] = None,
        goal_tier: Optional[str] = None,
        cycle_id: Optional[str] = None,
    ) -> tuple[str, float, Optional[ConstitutionalDecision]]:
        """Pre-screen a goal before it enters ranking.

        Returns (verdict, score_adjustment, decision).
        - allow:     0.0 adjustment — goal proceeds normally
        - caution:  -0.3 adjustment — goal is downgraded
        - reject:   goal should be excluded from ranking
        - requires_human_override: goal needs Matt's approval
        """
        decision = await self.evaluate(
            subject_type="goal",
            subject_id=goal_id,
            subject_summary=f"Goal: {goal_title} (tier={goal_tier})",
            context={"goal_tier": goal_tier or ""},
            cycle_id=cycle_id,
        )

        verdict = str(decision.verdict)
        score_adj = 0.0

        if verdict == "reject":
            # Immutable principle violation — block the goal
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="goal",
                target_id=goal_id,
                target_summary=goal_title,
                action="blocked",
                action_detail=str(decision.explanation),
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "blocked"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            logger.warning(f"Goal BLOCKED by covenant: {goal_title}")
            return "reject", -999.0, decision

        if verdict == "caution":
            # Mutable conflict — downgrade score
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="goal",
                target_id=goal_id,
                target_summary=goal_title,
                action="downgraded",
                action_detail=str(decision.explanation),
                original_score=0.0,  # actual score applied in caller
                adjusted_score=-0.3,
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "downgraded"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            score_adj = -0.3
            return "caution", score_adj, decision

        # allow — no enforcement needed
        decision.enforcement_action = "none"  # type: ignore[assignment]
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
        return "allow", 0.0, decision

    async def enforce_candidate(
        self,
        candidate_title: str,
        candidate_id: Optional[str] = None,
        candidate_score: float = 0.0,
        action_type: Optional[str] = None,
        goal_tier: Optional[str] = None,
        cycle_id: Optional[str] = None,
    ) -> tuple[str, Optional[CovenantEnforcementRecord]]:
        """Pre-screen a selected next-action candidate before execution gate.

        Returns (verdict, enforcement_record).
        - allow:                  proceed to execution gate
        - blocked:                candidate cannot proceed
        - requires_human_override: needs Matt's approval before execution
        """
        context: Dict[str, Any] = {
            "action_type": action_type or "",
            "goal_tier": goal_tier or "",
            "candidate_score": candidate_score,
        }

        # Strategic/mission candidates that trigger HOP principle → require override
        if goal_tier in ("mission", "strategic"):
            context["requires_human_override"] = True

        decision = await self.evaluate(
            subject_type="candidate",
            subject_id=candidate_id,
            subject_summary=(
                f"Candidate: {candidate_title} "
                f"(score={candidate_score:.4f}, type={action_type}, tier={goal_tier})"
            ),
            context=context,
            cycle_id=cycle_id,
        )

        verdict = str(decision.verdict)

        if verdict == "reject":
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="candidate",
                target_id=candidate_id,
                target_summary=candidate_title,
                action="blocked",
                action_detail=str(decision.explanation),
                original_score=candidate_score,
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "blocked"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            logger.warning(f"Candidate BLOCKED by covenant: {candidate_title}")
            return "blocked", enforcement

        if verdict == "requires_human_override":
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="candidate",
                target_id=candidate_id,
                target_summary=candidate_title,
                action="override_requested",
                action_detail=str(decision.explanation),
                original_score=candidate_score,
                override_status="pending",
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "override_requested"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            logger.info(f"Candidate requires HUMAN OVERRIDE: {candidate_title}")
            return "requires_human_override", enforcement

        # allow or caution — proceed (caution is logged but not blocking at candidate stage)
        decision.enforcement_action = "none"  # type: ignore[assignment]
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
        return "allow", None

    async def enforce_execution(
        self,
        candidate_title: str,
        candidate_id: Optional[str] = None,
        classification: str = "executable",
        goal_tier: Optional[str] = None,
        cycle_id: Optional[str] = None,
    ) -> tuple[str, Optional[CovenantEnforcementRecord]]:
        """Final veto check before execution begins.

        Returns (verdict, enforcement_record).
        - allow:                  proceed with execution
        - vetoed:                 execution must not proceed
        - requires_human_override: needs Matt's explicit approval
        """
        context: Dict[str, Any] = {
            "execution_classification": classification,
            "goal_tier": goal_tier or "",
        }

        # If classified executable but it's mission/strategic, flag for override
        if classification == "executable" and goal_tier in ("mission", "strategic"):
            context["requires_human_override"] = True

        decision = await self.evaluate(
            subject_type="execution",
            subject_id=candidate_id,
            subject_summary=(
                f"Execution: {candidate_title} "
                f"(classification={classification}, tier={goal_tier})"
            ),
            context=context,
            cycle_id=cycle_id,
        )

        verdict = str(decision.verdict)

        if verdict == "reject":
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="execution",
                target_id=candidate_id,
                target_summary=candidate_title,
                action="vetoed",
                action_detail=str(decision.explanation),
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "vetoed"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            logger.warning(f"Execution VETOED by covenant: {candidate_title}")
            return "vetoed", enforcement

        if verdict == "requires_human_override":
            enforcement = CovenantEnforcementRecord(
                decision_id=str(decision.id),
                target_type="execution",
                target_id=candidate_id,
                target_summary=candidate_title,
                action="override_requested",
                action_detail=str(decision.explanation),
                override_status="pending",
                cycle_id=cycle_id,
            )
            decision.enforcement_action = "override_requested"  # type: ignore[assignment]
            self.db.add(enforcement)
            try:
                await self.db.commit()
                await self.db.refresh(enforcement)
            except Exception:
                await self.db.rollback()
            logger.info(f"Execution requires HUMAN OVERRIDE: {candidate_title}")
            return "requires_human_override", enforcement

        # allow / caution — proceed
        decision.enforcement_action = "none"  # type: ignore[assignment]
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
        return "allow", None

    # ------------------------------------------------------------------
    # Enforcement read-only queries
    # ------------------------------------------------------------------
    async def get_recent_enforcement(
        self, limit: int = 10
    ) -> List[CovenantEnforcementRecord]:
        """Return recent enforcement records, newest first."""
        stmt = (
            select(CovenantEnforcementRecord)
            .order_by(CovenantEnforcementRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_blocked_or_vetoed(
        self, limit: int = 10
    ) -> List[CovenantEnforcementRecord]:
        """Return blocked/vetoed enforcement actions."""
        stmt = (
            select(CovenantEnforcementRecord)
            .where(CovenantEnforcementRecord.action.in_(["blocked", "vetoed"]))
            .order_by(CovenantEnforcementRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_override_requests(
        self, limit: int = 10
    ) -> List[CovenantEnforcementRecord]:
        """Return override-requested enforcement actions."""
        stmt = (
            select(CovenantEnforcementRecord)
            .where(CovenantEnforcementRecord.action == "override_requested")
            .order_by(CovenantEnforcementRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Phase 11: Override Resolution — Human Covenant Interface
    # ------------------------------------------------------------------

    async def resolve_override(
        self,
        record_id: str,
        resolution: str,
        resolver: str,
        rationale: str,
    ) -> Optional[CovenantEnforcementRecord]:
        """Resolve an override request: approve, deny, expire, or revoke.

        Only records with override_status='pending' can be resolved
        (except 'revoke' which can act on 'approved' records).

        Returns the updated record or None if not found / invalid state.
        """
        valid_resolutions = {"approved", "denied", "expired", "revoked"}
        if resolution not in valid_resolutions:
            logger.warning(f"Invalid resolution '{resolution}' for record {record_id}")
            return None

        stmt = select(CovenantEnforcementRecord).where(
            CovenantEnforcementRecord.id == record_id
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            logger.info(f"Override record not found: {record_id}")
            return None

        # State machine: pending → approved/denied/expired; approved → revoked
        if resolution == "revoked":
            if record.override_status != "approved":
                logger.warning(
                    f"Cannot revoke record {record_id}: "
                    f"status is '{record.override_status}', not 'approved'"
                )
                return None
        else:
            if record.override_status != "pending":
                logger.warning(
                    f"Cannot resolve record {record_id}: "
                    f"status is '{record.override_status}', not 'pending'"
                )
                return None

        from datetime import datetime

        record.override_status = resolution
        record.resolution_outcome = resolution
        record.override_resolved_at = datetime.utcnow()
        record.resolver_identity = resolver
        record.human_rationale = rationale

        try:
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(
                f"Override {record_id} resolved: {resolution} "
                f"by {resolver}"
            )
        except Exception:
            await self.db.rollback()
            logger.exception(f"Failed to resolve override {record_id}")
            return None

        return record

    async def expire_stale_overrides(
        self, max_age_hours: int = 24
    ) -> List[CovenantEnforcementRecord]:
        """Auto-expire pending overrides older than max_age_hours.

        Returns list of expired records.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        stmt = select(CovenantEnforcementRecord).where(
            CovenantEnforcementRecord.override_status == "pending",
            CovenantEnforcementRecord.created_at < cutoff,
        )
        result = await self.db.execute(stmt)
        stale = list(result.scalars().all())

        now = datetime.utcnow()
        for record in stale:
            record.override_status = "expired"
            record.resolution_outcome = "expired"
            record.override_resolved_at = now
            record.resolver_identity = "system:expiry"
            record.human_rationale = (
                f"Auto-expired after {max_age_hours}h without resolution."
            )

        if stale:
            try:
                await self.db.commit()
                logger.info(f"Expired {len(stale)} stale override requests")
            except Exception:
                await self.db.rollback()
                logger.exception("Failed to expire stale overrides")
                return []

        return stale

    async def get_pending_overrides(
        self, limit: int = 10
    ) -> List[CovenantEnforcementRecord]:
        """Return pending override requests, oldest first (FIFO)."""
        stmt = (
            select(CovenantEnforcementRecord)
            .where(CovenantEnforcementRecord.override_status == "pending")
            .order_by(CovenantEnforcementRecord.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_resolved_overrides(
        self, limit: int = 10
    ) -> List[CovenantEnforcementRecord]:
        """Return resolved override records, newest first."""
        stmt = (
            select(CovenantEnforcementRecord)
            .where(
                CovenantEnforcementRecord.override_status.in_(
                    ["approved", "denied", "expired", "revoked"]
                )
            )
            .order_by(CovenantEnforcementRecord.override_resolved_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
