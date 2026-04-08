"""Memory retrieval doctrine for prompt-facing Kor'tana surfaces.

This service defines which durable memory lanes may influence each surface:

  reflection / self_direction:
    - SelfMemory only
    - no conversation replay
    - no incident replay

  chat:
    - SelfMemory for continuity of self
    - recent conversation_messages for cross-session continuity
    - unresolved IncidentMemory for honest risk/state awareness

  patch_analysis:
    - ArchitectureMemory for repository structure and risk context
    - related IncidentMemory for prior failures and repair history
    - no self-memory or conversation replay

  operational:
    - no durable persona memory at all

The generic `memories` table exposed through MemoryEngine remains an explicit
introspection/diagnostics lane. It is not auto-injected into chat, reflection,
or operational prompts until a dedicated consumer opts into it.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

from sqlalchemy import desc, select

from src.kortana.models import (
    ArchitectureMemory,
    ConversationMessage,
    IncidentMemory,
    SelfMemory,
)


class MemorySurface(str, Enum):
    REFLECTION = "reflection"
    SELF_DIRECTION = "self_direction"
    CHAT = "chat"
    PATCH_ANALYSIS = "patch_analysis"
    OPERATIONAL = "operational"


@dataclass(frozen=True)
class MemoryPolicySpec:
    self_memory_limit: int = 0
    include_conversation: bool = False
    conversation_limit: int = 0
    include_incidents: bool = False
    incident_limit: int = 0
    include_architecture: bool = False
    architecture_limit: int = 0
    include_related_incidents: bool = False
    related_incident_limit: int = 0
    include_knowledge_graph: bool = False
    knowledge_graph_limit: int = 0


@dataclass
class MemoryPolicyContext:
    self_memory_lines: list[str] = field(default_factory=list)
    conversation_lines: list[str] = field(default_factory=list)
    incident_lines: list[str] = field(default_factory=list)
    architecture_lines: list[str] = field(default_factory=list)
    related_incident_lines: list[str] = field(default_factory=list)
    knowledge_graph_lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        sections: list[str] = []
        if self_memory_lines := self.self_memory_lines:
            sections.append("## continuity of self\n" + "\n".join(self_memory_lines))
        if conversation_lines := self.conversation_lines:
            sections.append(
                "## recent conversation continuity\n"
                + "\n".join(conversation_lines)
            )
        if incident_lines := self.incident_lines:
            sections.append(
                "## unresolved incident memory\n" + "\n".join(incident_lines)
            )
        if architecture_lines := self.architecture_lines:
            sections.append(
                "## relevant architecture memory\n" + "\n".join(architecture_lines)
            )
        if related_incident_lines := self.related_incident_lines:
            sections.append(
                "## related incident history\n"
                + "\n".join(related_incident_lines)
            )
        if knowledge_graph_lines := self.knowledge_graph_lines:
            sections.append(
                "## structured knowledge\n" + "\n".join(knowledge_graph_lines)
            )
        return "\n\n".join(sections)


class MemoryPolicyService:
    """Central policy for prompt-visible memory retrieval."""

    _POLICY_BY_SURFACE: dict[MemorySurface, MemoryPolicySpec] = {
        MemorySurface.REFLECTION: MemoryPolicySpec(self_memory_limit=3),
        MemorySurface.SELF_DIRECTION: MemoryPolicySpec(self_memory_limit=4),
        MemorySurface.CHAT: MemoryPolicySpec(
            self_memory_limit=2,
            include_conversation=True,
            conversation_limit=4,
            include_incidents=True,
            incident_limit=2,
            include_knowledge_graph=True,
            knowledge_graph_limit=3,
        ),
        MemorySurface.PATCH_ANALYSIS: MemoryPolicySpec(
            include_architecture=True,
            architecture_limit=3,
            include_related_incidents=True,
            related_incident_limit=3,
        ),
        MemorySurface.OPERATIONAL: MemoryPolicySpec(),
    }

    @classmethod
    def spec_for(cls, surface: MemorySurface) -> MemoryPolicySpec:
        return cls._POLICY_BY_SURFACE[surface]

    @classmethod
    async def build_context(
        cls,
        session: Any,
        *,
        surface: MemorySurface,
        query: str | None = None,
        session_id: str | None = None,
        incident: IncidentMemory | None = None,
        self_memory_limit: int | None = None,
        include_conversation: bool | None = None,
        include_incidents: bool | None = None,
        include_architecture: bool | None = None,
        include_related_incidents: bool | None = None,
    ) -> MemoryPolicyContext:
        spec = cls.spec_for(surface)
        resolved_self_memory_limit = (
            spec.self_memory_limit if self_memory_limit is None else self_memory_limit
        )
        resolved_include_conversation = (
            spec.include_conversation
            if include_conversation is None
            else include_conversation
        )
        resolved_include_incidents = (
            spec.include_incidents if include_incidents is None else include_incidents
        )
        resolved_include_architecture = (
            spec.include_architecture
            if include_architecture is None
            else include_architecture
        )
        resolved_include_related_incidents = (
            spec.include_related_incidents
            if include_related_incidents is None
            else include_related_incidents
        )

        context = MemoryPolicyContext()

        if resolved_self_memory_limit > 0:
            self_memories = await cls.semantic_self_memory(
                session,
                query=query,
                limit=resolved_self_memory_limit,
            )
            context.self_memory_lines = [
                "- "
                f"[cycle {memory.cycle_number}] "
                f"{cls._truncate(cast(str | None, memory.summary), 220)}"
                for memory in self_memories
            ]

        if (
            resolved_include_conversation
            and session_id
            and spec.conversation_limit > 0
        ):
            messages = await cls.recent_conversation(
                session,
                session_id=session_id,
                limit=spec.conversation_limit,
            )
            context.conversation_lines = [
                "- "
                f"{cast(str, message.role)}: "
                f"{cls._truncate(cast(str | None, message.content), 180)}"
                for message in messages
            ]

        if resolved_include_incidents and spec.incident_limit > 0:
            incidents = await cls.unresolved_incidents(
                session,
                limit=spec.incident_limit,
            )
            context.incident_lines = [
                "- "
                f"[{cast(str, incident.incident_type)}] "
                f"{cls._truncate(cast(str | None, incident.description), 180)}"
                for incident in incidents
            ]

        if resolved_include_architecture and spec.architecture_limit > 0:
            memories = await cls.relevant_architecture_memory(
                session,
                query=query,
                limit=spec.architecture_limit,
            )
            context.architecture_lines = [
                cls._format_architecture_line(memory) for memory in memories
            ]

        if (
            resolved_include_related_incidents
            and incident is not None
            and spec.related_incident_limit > 0
        ):
            related_incidents = await cls.related_incidents(
                session,
                incident=incident,
                limit=spec.related_incident_limit,
            )
            context.related_incident_lines = [
                cls._format_related_incident_line(entry)
                for entry in related_incidents
            ]

        # Knowledge graph — structured facts (Phase 11)
        if spec.include_knowledge_graph and spec.knowledge_graph_limit > 0 and query:
            try:
                from src.kortana.services.knowledge_graph import KnowledgeGraphService

                kg = KnowledgeGraphService(session)
                kg_text = await kg.query_context(query, limit=spec.knowledge_graph_limit)
                if kg_text:
                    context.knowledge_graph_lines = [
                        f"- {line}" for line in kg_text.split("\n") if line.strip()
                    ]
            except Exception:
                pass  # knowledge graph is best-effort

        return context

    @staticmethod
    async def semantic_self_memory(
        session: Any,
        *,
        query: str | None = None,
        limit: int = 5,
    ) -> list[SelfMemory]:
        """Return the most relevant SelfMemory rows for a prompt surface."""
        try:
            if query is not None:
                query_vec = MemoryPolicyService._embed_text(query)
                if query_vec is not None:
                    stmt = select(SelfMemory).where(SelfMemory.embedding.isnot(None))
                    result = await session.execute(stmt)
                    candidates = cast(
                        list[SelfMemory], list(result.scalars().all())
                    )
                    if candidates:
                        scored = [
                            (
                                memory,
                                MemoryPolicyService._cosine_similarity(
                                    query_vec, cast(list[float], memory.embedding)
                                ),
                            )
                            for memory in candidates
                            if memory.embedding
                        ]
                        scored.sort(key=lambda item: item[1], reverse=True)
                        return [memory for memory, _ in scored[:limit]]

            stmt = (
                select(SelfMemory).order_by(SelfMemory.created_at.desc()).limit(limit)
            )
            result = await session.execute(stmt)
            memories = cast(list[SelfMemory], list(result.scalars().all()))
            return list(reversed(memories))
        except Exception:
            return []

    @staticmethod
    async def recent_conversation(
        session: Any,
        *,
        session_id: str,
        limit: int = 4,
    ) -> list[ConversationMessage]:
        try:
            stmt = (
                select(ConversationMessage)
                .where(ConversationMessage.session_id == session_id)
                .order_by(desc(ConversationMessage.created_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            messages = cast(list[ConversationMessage], list(result.scalars().all()))
            return list(reversed(messages))
        except Exception:
            return []

    @staticmethod
    async def unresolved_incidents(
        session: Any,
        *,
        limit: int = 2,
    ) -> list[IncidentMemory]:
        try:
            stmt = (
                select(IncidentMemory)
                .where(IncidentMemory.resolved.is_(False))
                .order_by(desc(IncidentMemory.created_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            return cast(list[IncidentMemory], list(result.scalars().all()))
        except Exception:
            return []

    @staticmethod
    async def relevant_architecture_memory(
        session: Any,
        *,
        query: str | None = None,
        limit: int = 3,
    ) -> list[ArchitectureMemory]:
        try:
            stmt = (
                select(ArchitectureMemory)
                .order_by(
                    desc(ArchitectureMemory.confidence_score),
                    desc(ArchitectureMemory.last_analyzed_at),
                )
                .limit(max(limit * 8, 12))
            )
            result = await session.execute(stmt)
            candidates = cast(
                list[ArchitectureMemory], list(result.scalars().all())
            )
            if not candidates:
                return []

            query_tokens = MemoryPolicyService._tokenize(query or "")
            if not query_tokens:
                return candidates[:limit]

            query_text = (query or "").lower()
            scored: list[tuple[ArchitectureMemory, float]] = []
            for memory in candidates:
                component_name = cast(str | None, memory.component_name) or ""
                knowledge_text = MemoryPolicyService._knowledge_text(
                    memory.knowledge_factors
                )
                haystack = " ".join(
                    part
                    for part in (
                        component_name,
                        cast(str | None, memory.description) or "",
                        knowledge_text,
                    )
                    if part
                )
                lexical_score = MemoryPolicyService._token_overlap_score(
                    query_tokens, haystack
                )
                if component_name and component_name.lower() in query_text:
                    lexical_score += 1.5
                if lexical_score <= 0.0:
                    continue

                confidence = float(
                    cast(float | None, memory.confidence_score) or 0.0
                )
                scored.append((memory, lexical_score + (confidence * 0.25)))

            scored.sort(key=lambda item: item[1], reverse=True)
            return [memory for memory, _ in scored[:limit]]
        except Exception:
            return []

    @staticmethod
    async def related_incidents(
        session: Any,
        *,
        incident: IncidentMemory,
        limit: int = 3,
    ) -> list[IncidentMemory]:
        try:
            stmt = select(IncidentMemory).order_by(desc(IncidentMemory.created_at))
            if incident.id is not None:
                stmt = stmt.where(IncidentMemory.id != incident.id)
            stmt = stmt.limit(max(limit * 10, 20))
            result = await session.execute(stmt)
            candidates = cast(list[IncidentMemory], list(result.scalars().all()))
            if not candidates:
                return []

            query_tokens = MemoryPolicyService._tokenize(
                " ".join(
                    part
                    for part in (
                        cast(str | None, incident.incident_type) or "",
                        cast(str | None, incident.description) or "",
                        cast(str | None, incident.stack_trace) or "",
                    )
                    if part
                )
            )
            scored: list[tuple[IncidentMemory, float]] = []
            current_type = cast(str | None, incident.incident_type) or ""

            for candidate in candidates:
                candidate_type = cast(str | None, candidate.incident_type) or ""
                candidate_text = " ".join(
                    part
                    for part in (
                        candidate_type,
                        cast(str | None, candidate.description) or "",
                        cast(str | None, candidate.resolution_strategy) or "",
                    )
                    if part
                )
                overlap_score = (
                    MemoryPolicyService._token_overlap_score(
                        query_tokens, candidate_text
                    )
                    if query_tokens
                    else 0.0
                )
                same_type_bonus = 2.0 if current_type and candidate_type == current_type else 0.0
                if same_type_bonus <= 0.0 and overlap_score <= 0.0:
                    continue

                strategy_bonus = (
                    0.75
                    if candidate.resolved and candidate.resolution_strategy
                    else 0.25
                    if candidate.resolution_strategy
                    else 0.0
                )
                scored.append(
                    (
                        candidate,
                        same_type_bonus + overlap_score + strategy_bonus,
                    )
                )

            scored.sort(key=lambda item: item[1], reverse=True)
            return [candidate for candidate, _ in scored[:limit]]
        except Exception:
            return []

    @staticmethod
    def _embed_text(text: str) -> list[float] | None:
        try:
            from src.kortana.services.gemini import gemini_service

            return gemini_service.embed_text(text)
        except Exception:
            return None

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def _truncate(text: str | None, limit: int) -> str:
        normalized = " ".join((text or "").split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    @classmethod
    def _format_architecture_line(cls, memory: ArchitectureMemory) -> str:
        component_name = cast(str | None, memory.component_name) or "unknown_component"
        description = cls._truncate(cast(str | None, memory.description), 180)
        factors = cls._truncate(cls._knowledge_text(memory.knowledge_factors), 120)
        confidence = float(cast(float | None, memory.confidence_score) or 0.0)
        line = f"- [{component_name}] {description} (confidence {confidence:.2f})"
        if factors:
            line += f" | factors: {factors}"
        return line

    @classmethod
    def _format_related_incident_line(cls, incident: IncidentMemory) -> str:
        incident_type = cast(str | None, incident.incident_type) or "unknown"
        status = "resolved" if incident.resolved else cast(str | None, incident.fix_status) or "open"
        description = cls._truncate(cast(str | None, incident.description), 160)
        strategy = cls._truncate(cast(str | None, incident.resolution_strategy), 120)
        line = f"- [{incident_type}, {status}] {description}"
        if strategy:
            line += f" | strategy: {strategy}"
        return line

    @staticmethod
    def _token_overlap_score(query_tokens: set[str], text: str) -> float:
        if not query_tokens:
            return 0.0
        text_tokens = MemoryPolicyService._tokenize(text)
        if not text_tokens:
            return 0.0
        overlap = query_tokens & text_tokens
        return len(overlap) / max(len(query_tokens), 1)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9_]+", text.lower())
            if len(token) > 2
        }

    @classmethod
    def _knowledge_text(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            return " ".join(
                f"{key} {cls._knowledge_text(item)}"
                for key, item in value.items()
            )
        if isinstance(value, list):
            return " ".join(cls._knowledge_text(item) for item in value)
        return str(value)
