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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import (
    ConstitutionalDecision,
    ConstitutionalPrinciple,
    CovenantEnforcementRecord,
    OverrideAuditRecord,
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Phase 12: Authority Policy — Trust Calibration
#
# Deterministic, in-code authority configuration.
# Maps resolver identities to authority tiers and defines
# which resolutions require which minimum tier.
#
# Tier hierarchy (highest → lowest): owner > operator > system
# ------------------------------------------------------------------

AUTHORITY_TIERS: Dict[str, int] = {
    "owner": 100,  # Matt — full authority
    "operator": 50,  # trusted operators — limited resolution
    "system": 10,  # automated processes — expiry only
}

# Map resolver identities to their authority tier
RESOLVER_AUTHORITY: Dict[str, str] = {
    "matt": "owner",
    "system:expiry": "system",
    "system:sweep": "system",
}

# Map resolution actions to minimum required tier
RESOLUTION_REQUIRED_TIER: Dict[str, str] = {
    "approved": "owner",  # only Matt can approve
    "denied": "owner",  # only Matt can deny
    "revoked": "owner",  # only Matt can revoke
    "expired": "system",  # automated or anyone above
}


# ------------------------------------------------------------------
# Phase 13: Auth-Bound Resolver Identity
#
# Trusted resolver context derived from authenticated user state
# or known system actor identity — never from caller-provided text.
# ------------------------------------------------------------------


@dataclass(frozen=True)
class ResolverContext:
    """Trusted resolver identity for override resolution.

    For human resolvers: built from authenticated TokenData + User record.
    For system actors: built from known system actor names.
    """

    actor_type: str  # "human" | "system"
    actor_name: str  # e.g. "matt", "system:expiry"
    user_id: Optional[str]  # User.id if human, None if system
    authority_tier: str  # derived from trusted source


def resolve_context_for_system(actor_name: str) -> ResolverContext:
    """Build a ResolverContext for a known system actor.

    System actors have deterministic tier from RESOLVER_AUTHORITY.
    Unknown system actors get no tier (will fail authority checks).
    """
    tier = RESOLVER_AUTHORITY.get(actor_name)
    return ResolverContext(
        actor_type="system",
        actor_name=actor_name,
        user_id=None,
        authority_tier=tier or "",
    )


async def resolve_context_from_user(
    token_data: Any, db: AsyncSession
) -> ResolverContext:
    """Build a ResolverContext from an authenticated user.

    Derives authority tier from the actual User record:
      - is_superuser=True → owner
      - is_active regular user → operator
      - fallback → no authority (empty string, will fail checks)

    Also checks RESOLVER_AUTHORITY for username-based overrides.
    """
    from src.kortana.models import User

    user_id: Optional[str] = None
    actor_name: str = token_data.email or token_data.username or "unknown"
    tier: str = ""

    # Look up the real user record for trusted state
    if token_data.user_id:
        stmt = select(User).where(User.id == str(token_data.user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is not None:
            user_id = str(user.id)
            actor_name = user.username or user.email

            # Derive tier from trusted DB state
            if user.is_superuser:
                tier = "owner"
            elif user.is_active:
                tier = "operator"

    # Allow RESOLVER_AUTHORITY override (e.g. "matt" → "owner" even if
    # DB doesn't have is_superuser set for some reason)
    policy_tier = RESOLVER_AUTHORITY.get(actor_name)
    if policy_tier and AUTHORITY_TIERS.get(policy_tier, 0) > AUTHORITY_TIERS.get(
        tier, 0
    ):
        tier = policy_tier

    return ResolverContext(
        actor_type="human",
        actor_name=actor_name,
        user_id=user_id,
        authority_tier=tier,
    )


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
    # Phase 11+12+13: Override Resolution with Auth-Bound Authority
    # ------------------------------------------------------------------

    async def _record_audit(
        self,
        enforcement_record_id: Optional[str],
        resolver: str,
        authority_tier: Optional[str],
        required_tier: Optional[str],
        action_attempted: str,
        outcome: str,
        detail: Optional[str] = None,
        cycle_id: Optional[str] = None,
        resolver_context: Optional["ResolverContext"] = None,
    ) -> OverrideAuditRecord:
        """Persist an audit record for an override resolution attempt.

        When resolver_context is provided, trusted identity fields
        (resolver_user_id, resolver_actor_type) are captured.
        """
        audit = OverrideAuditRecord(
            enforcement_record_id=enforcement_record_id,
            resolver_identity=resolver,
            resolver_user_id=(resolver_context.user_id if resolver_context else None),
            resolver_actor_type=(
                resolver_context.actor_type if resolver_context else None
            ),
            authority_tier=authority_tier,
            required_tier=required_tier,
            action_attempted=action_attempted,
            outcome=outcome,
            detail=detail,
            cycle_id=cycle_id,
        )
        self.db.add(audit)
        try:
            await self.db.commit()
            await self.db.refresh(audit)
        except Exception:
            await self.db.rollback()
            logger.exception("Failed to persist audit record")
        return audit

    def _get_resolver_tier(self, resolver: str) -> Optional[str]:
        """Look up the authority tier for a resolver identity."""
        return RESOLVER_AUTHORITY.get(resolver)

    def _has_sufficient_authority(
        self, resolver_tier: Optional[str], required_tier: str
    ) -> bool:
        """Check if resolver_tier meets or exceeds required_tier."""
        if resolver_tier is None:
            return False
        resolver_level = AUTHORITY_TIERS.get(resolver_tier, 0)
        required_level = AUTHORITY_TIERS.get(required_tier, 999)
        return resolver_level >= required_level

    async def resolve_override(
        self,
        record_id: str,
        resolution: str,
        resolver: str,
        rationale: str,
        resolver_context: Optional["ResolverContext"] = None,
    ) -> Optional[CovenantEnforcementRecord]:
        """Resolve an override request with authority check and audit trail.

        When resolver_context is provided (Phase 13), authority is derived
        from the trusted context. Otherwise falls back to string-based
        RESOLVER_AUTHORITY lookup (Phase 12 compat).

        Returns the updated record or None if unauthorized / invalid state.
        """
        valid_resolutions = {"approved", "denied", "expired", "revoked"}
        if resolution not in valid_resolutions:
            logger.warning(f"Invalid resolution '{resolution}' for record {record_id}")
            return None

        # --- Derive authority from context or string ---
        if resolver_context is not None:
            resolver_tier: Optional[str] = resolver_context.authority_tier or None
            resolver = resolver_context.actor_name
        else:
            resolver_tier = self._get_resolver_tier(resolver)

        required_tier = RESOLUTION_REQUIRED_TIER.get(resolution, "owner")

        if resolver_tier is None:
            # Unknown resolver — unauthorized
            logger.warning(
                f"Unauthorized resolver '{resolver}' attempted "
                f"'{resolution}' on record {record_id}"
            )
            await self._record_audit(
                enforcement_record_id=record_id,
                resolver=resolver,
                authority_tier=None,
                required_tier=required_tier,
                action_attempted=resolution,
                outcome="unauthorized",
                detail=f"Resolver '{resolver}' not in authority policy.",
                resolver_context=resolver_context,
            )
            return None

        if not self._has_sufficient_authority(resolver_tier, required_tier):
            logger.warning(
                f"Insufficient authority: '{resolver}' (tier={resolver_tier}) "
                f"attempted '{resolution}' requiring tier={required_tier}"
            )
            await self._record_audit(
                enforcement_record_id=record_id,
                resolver=resolver,
                authority_tier=resolver_tier,
                required_tier=required_tier,
                action_attempted=resolution,
                outcome="insufficient_authority",
                detail=(
                    f"Resolver '{resolver}' has tier '{resolver_tier}' "
                    f"but '{resolution}' requires '{required_tier}'."
                ),
                resolver_context=resolver_context,
            )
            return None

        # --- Load record ---
        stmt = select(CovenantEnforcementRecord).where(
            CovenantEnforcementRecord.id == record_id
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            logger.info(f"Override record not found: {record_id}")
            await self._record_audit(
                enforcement_record_id=None,
                resolver=resolver,
                authority_tier=resolver_tier,
                required_tier=required_tier,
                action_attempted=resolution,
                outcome="not_found",
                detail=f"Enforcement record {record_id} does not exist.",
                resolver_context=resolver_context,
            )
            return None

        # --- State machine: pending → approved/denied/expired; approved → revoked ---
        if resolution == "revoked":
            if record.override_status != "approved":
                logger.warning(
                    f"Cannot revoke record {record_id}: "
                    f"status is '{record.override_status}', not 'approved'"
                )
                await self._record_audit(
                    enforcement_record_id=record_id,
                    resolver=resolver,
                    authority_tier=resolver_tier,
                    required_tier=required_tier,
                    action_attempted=resolution,
                    outcome="invalid_state",
                    detail=(
                        f"Cannot revoke: status is '{record.override_status}', "
                        f"not 'approved'."
                    ),
                    cycle_id=record.cycle_id,
                    resolver_context=resolver_context,
                )
                return None
        else:
            if record.override_status != "pending":
                logger.warning(
                    f"Cannot resolve record {record_id}: "
                    f"status is '{record.override_status}', not 'pending'"
                )
                await self._record_audit(
                    enforcement_record_id=record_id,
                    resolver=resolver,
                    authority_tier=resolver_tier,
                    required_tier=required_tier,
                    action_attempted=resolution,
                    outcome="invalid_state",
                    detail=(
                        f"Cannot '{resolution}': status is "
                        f"'{record.override_status}', not 'pending'."
                    ),
                    cycle_id=record.cycle_id,
                    resolver_context=resolver_context,
                )
                return None

        # --- Apply resolution with trusted identity ---
        from datetime import datetime

        record.override_status = resolution
        record.resolution_outcome = resolution
        record.override_resolved_at = datetime.utcnow()
        record.resolver_identity = resolver
        record.human_rationale = rationale
        if resolver_context is not None:
            record.resolver_user_id = resolver_context.user_id
            record.resolver_actor_type = resolver_context.actor_type

        try:
            await self.db.commit()
            await self.db.refresh(record)
            logger.info(f"Override {record_id} resolved: {resolution} by {resolver}")
        except Exception:
            await self.db.rollback()
            logger.exception(f"Failed to resolve override {record_id}")
            return None

        # --- Record authorized audit ---
        await self._record_audit(
            enforcement_record_id=record_id,
            resolver=resolver,
            authority_tier=resolver_tier,
            required_tier=required_tier,
            action_attempted=resolution,
            outcome="authorized",
            detail=f"Resolved: {resolution}. Rationale: {rationale}",
            cycle_id=record.cycle_id,
            resolver_context=resolver_context,
        )

        # --- Feed outcome back into the learning loop ---
        try:
            from src.kortana.services.outcome_learning_service import (
                OutcomeLearningService,
            )

            ols = OutcomeLearningService(self.db)
            await ols.learn_from_override_resolution(
                enforcement_record=record,
                cycle_id=record.cycle_id,
            )
        except Exception:
            logger.exception(
                f"Non-fatal: outcome learning from override {record_id} failed"
            )

        return record

    async def expire_stale_overrides(
        self, max_age_hours: int = 24
    ) -> List[CovenantEnforcementRecord]:
        """Auto-expire pending overrides older than max_age_hours.

        Records system_expiry audit for each expired record.
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
        expiry_ctx = resolve_context_for_system("system:expiry")
        for record in stale:
            record.override_status = "expired"
            record.resolution_outcome = "expired"
            record.override_resolved_at = now
            record.resolver_identity = "system:expiry"
            record.resolver_user_id = None
            record.resolver_actor_type = "system"
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

            # Record audit entries for each expired record
            for record in stale:
                await self._record_audit(
                    enforcement_record_id=str(record.id),
                    resolver="system:expiry",
                    authority_tier="system",
                    required_tier="system",
                    action_attempted="expired",
                    outcome="system_expiry",
                    detail=f"Auto-expired after {max_age_hours}h.",
                    cycle_id=str(record.cycle_id) if record.cycle_id else None,
                    resolver_context=expiry_ctx,
                )

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

    # ------------------------------------------------------------------
    # Phase 12: Authority Audit Queries
    # ------------------------------------------------------------------

    async def get_audit_history(self, limit: int = 20) -> List[OverrideAuditRecord]:
        """Return recent audit records, newest first."""
        stmt = (
            select(OverrideAuditRecord)
            .order_by(OverrideAuditRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unauthorized_attempts(
        self, limit: int = 20
    ) -> List[OverrideAuditRecord]:
        """Return unauthorized or insufficient-authority resolution attempts."""
        stmt = (
            select(OverrideAuditRecord)
            .where(
                OverrideAuditRecord.outcome.in_(
                    ["unauthorized", "insufficient_authority"]
                )
            )
            .order_by(OverrideAuditRecord.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def get_authority_policy() -> Dict[str, Any]:
        """Return the current authority policy configuration."""
        return {
            "tiers": AUTHORITY_TIERS,
            "resolver_authority": RESOLVER_AUTHORITY,
            "resolution_required_tier": RESOLUTION_REQUIRED_TIER,
        }
