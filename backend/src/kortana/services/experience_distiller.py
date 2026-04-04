"""
KOR'TANA Experience Distiller — Phase 8 Cycle #3: Generational Memory
Summarises operational data into reusable "experience capsules".
Implements cost-aware API throttling and memory compaction.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.model_lane_policy import describe_model_lane
from src.kortana.models import AuditLog, Memory
from src.kortana.provider_model_defaults import LLM_ROUTER_GEMINI_MODEL
from src.kortana.services.gemini_config import get_preferred_model_name

logger = logging.getLogger(__name__)

DISTILL_MODEL = LLM_ROUTER_GEMINI_MODEL
# Tokens used in current session (in-memory counter, resets on restart)
_session_tokens_used = 0
_SESSION_TOKEN_BUDGET = 50_000  # conservative free-tier guard


class ExperienceCapsule:
    """A compressed insight distilled from multiple operational memories."""

    __slots__ = (
        "id",
        "created_at",
        "source_count",
        "insight",
        "category",
        "confidence",
        "source_ids",
    )

    def __init__(
        self,
        insight: str,
        category: str,
        source_count: int,
        confidence: float = 0.8,
        source_ids: Optional[List[str]] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.insight = insight
        self.category = category
        self.source_count = source_count
        self.confidence = confidence
        self.source_ids = source_ids or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "insight": self.insight,
            "category": self.category,
            "source_count": self.source_count,
            "confidence": self.confidence,
        }


def get_distillation_model_info() -> Dict[str, str]:
    """Return preferred and resolved Gemini model metadata for distillation."""
    resolved_model = get_preferred_model_name(DISTILL_MODEL)
    return {
        "preferred_model": DISTILL_MODEL,
        "model": resolved_model,
        "model_lane": describe_model_lane(resolved_model),
    }


async def _call_gemini_distill(prompt: str) -> Optional[str]:
    """Call Gemini to distil memories into an insight, respecting token budget."""
    global _session_tokens_used
    if _session_tokens_used >= _SESSION_TOKEN_BUDGET:
        logger.warning("Token budget exhausted — distillation paused")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model_info = get_distillation_model_info()
        response = client.models.generate_content(
            model=model_info["model"],
            contents=prompt,
        )
        # Rough token estimate (4 chars ≈ 1 token)
        _session_tokens_used += (len(prompt) + len(response.text or "")) // 4
        return response.text
    except Exception as e:
        logger.error(f"Gemini distillation call failed: {e}")
        return None


class ExperienceDistiller:
    """Compress old operational data into reusable experience capsules."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._capsules: List[ExperienceCapsule] = []

    # ------------------------------------------------------------------
    # Distil memories older than `age_hours` into capsules
    # ------------------------------------------------------------------
    async def distil(
        self,
        age_hours: int = 24,
        batch_size: int = 30,
    ) -> List[ExperienceCapsule]:
        """Summarise old memories into experience capsules."""
        cutoff = datetime.utcnow() - timedelta(hours=age_hours)

        # Fetch old memories
        stmt = (
            select(Memory)
            .where(Memory.created_at < cutoff)
            .order_by(Memory.created_at.asc())
            .limit(batch_size)
        )
        result = await self.db.execute(stmt)
        old_memories = result.scalars().all()

        if not old_memories:
            logger.info("No memories old enough to distil")
            return []

        # Group by memory_type
        groups: Dict[str, List[Memory]] = {}
        for mem in old_memories:
            groups.setdefault(str(mem.memory_type), []).append(mem)

        capsules: List[ExperienceCapsule] = []
        for mem_type, mems in groups.items():
            capsule = await self._distil_group(mem_type, mems)
            if capsule:
                capsules.append(capsule)
                self._capsules.append(capsule)

                # Store capsule as a long_term memory
                cap_mem = Memory(
                    agent_id="kortana-system",
                    memory_type="long_term",
                    content=f"[CAPSULE:{capsule.category}] {capsule.insight}",
                )
                self.db.add(cap_mem)

        if capsules:
            await self.db.commit()
            logger.info(
                f"Distilled {len(old_memories)} memories → " f"{len(capsules)} capsules"
            )

        return capsules

    async def _distil_group(
        self,
        category: str,
        memories: List[Memory],
    ) -> Optional[ExperienceCapsule]:
        """Summarise a group of memories into a single capsule."""
        contents = "\n".join(
            f"- [{m.created_at.isoformat()}] {m.content[:200]}" for m in memories
        )

        prompt = (
            "we are kor'tana's experience distiller. "
            "Compress these operational memories into ONE concise insight "
            "(max 2 sentences) that would help future autonomous decisions.\n\n"
            f"Category: {category}\n"
            f"Memory count: {len(memories)}\n"
            f"Memories:\n{contents}\n\n"
            "Respond with ONLY the insight, nothing else."
        )

        insight = await _call_gemini_distill(prompt)
        if not insight:
            # Fallback: simple concatenation summary
            insight = (
                f"Aggregated {len(memories)} {category} events. "
                f"Latest: {memories[-1].content[:150]}"
            )

        return ExperienceCapsule(
            insight=insight.strip(),
            category=category,
            source_count=len(memories),
            confidence=0.8 if insight else 0.5,
            source_ids=[str(m.id) for m in memories],
        )

    # ------------------------------------------------------------------
    # Compact: remove source memories after distillation
    # ------------------------------------------------------------------
    async def compact(self, capsule_ids: Optional[List[str]] = None) -> int:
        """Remove source memories whose insights are captured in capsules."""
        targets = (
            [c for c in self._capsules if c.id in capsule_ids]
            if capsule_ids
            else self._capsules
        )

        deleted = 0
        for capsule in targets:
            for src_id in capsule.source_ids:
                stmt = select(Memory).where(Memory.id == src_id)
                result = await self.db.execute(stmt)
                mem = result.scalar_one_or_none()
                if mem:
                    await self.db.delete(mem)
                    deleted += 1

        if deleted:
            await self.db.commit()
            logger.info(f"Compacted {deleted} source memories")
        return deleted

    # ------------------------------------------------------------------
    # Cost tracking
    # ------------------------------------------------------------------
    def get_cost_stats(self) -> Dict[str, Any]:
        """Return API token usage stats for budget awareness."""
        return {
            "session_tokens_used": _session_tokens_used,
            "session_token_budget": _SESSION_TOKEN_BUDGET,
            "budget_remaining": _SESSION_TOKEN_BUDGET - _session_tokens_used,
            "budget_pct_used": round(
                _session_tokens_used / _SESSION_TOKEN_BUDGET * 100, 1
            ),
            "capsules_created": len(self._capsules),
            **get_distillation_model_info(),
        }

    # ------------------------------------------------------------------
    # Get capsules
    # ------------------------------------------------------------------
    def get_capsules(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent experience capsules."""
        return [c.to_dict() for c in self._capsules[-limit:]]

    # ------------------------------------------------------------------
    # Diagnostic history distillation
    # ------------------------------------------------------------------
    async def distil_diagnostics(
        self, age_hours: int = 48
    ) -> Optional[ExperienceCapsule]:
        """Summarise old diagnostic audit logs into an experience capsule."""
        cutoff = datetime.utcnow() - timedelta(hours=age_hours)

        stmt = (
            select(AuditLog)
            .where(AuditLog.action == "self_diagnostic")
            .where(AuditLog.created_at < cutoff)
            .order_by(AuditLog.created_at.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        if not logs:
            return None

        items = []
        for log_entry in logs:
            details = cast(Dict[str, Any], log_entry.details or {})
            items.append(
                f"- {details.get('error_type', '?')}: "
                f"{details.get('root_cause', 'unknown')}"
            )

        prompt = (
            "Distil these KOR'TANA failure diagnostics into ONE operational insight "
            "(max 2 sentences) for future self-repair:\n\n"
            + "\n".join(items)
            + "\n\nRespond with ONLY the insight."
        )

        insight = await _call_gemini_distill(prompt)
        if not insight:
            insight = f"Aggregated {len(logs)} diagnostic events."

        capsule = ExperienceCapsule(
            insight=insight.strip(),
            category="diagnostics",
            source_count=len(logs),
        )
        self._capsules.append(capsule)
        return capsule
