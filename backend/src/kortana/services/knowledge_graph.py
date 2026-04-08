"""kor'tana's long-term cognitive memory graph.

extracts structured knowledge from conversations and maintains a living graph
of entities, relationships, and facts about matt's world.

this is what separates remembering that a conversation happened from actually
knowing what was learned from it.

tiers:
  - entities: people, projects, tools, concepts, preferences, places
  - relations: directed edges (matt --uses--> railway)
  - facts: discrete assertions with temporal validity and confidence decay

extraction uses groq (fast, free) with a structured JSON prompt.
embeddings use gemini (768d) for semantic entity lookup.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import (
    KnowledgeEntity,
    KnowledgeFact,
    KnowledgeRelation,
)
from src.kortana.services.memory_engine import generate_embedding

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# extraction prompt — instructs the LLM to return structured JSON
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM = """You are a knowledge extraction engine for an AI assistant named Kor'tana.
Given a conversation excerpt, extract structured knowledge as JSON.

Return ONLY a JSON object with these fields:
{
  "entities": [
    {
      "name": "exact name",
      "type": "person|project|tool|concept|preference|place|event|organisation",
      "summary": "one sentence description (optional)"
    }
  ],
  "relations": [
    {
      "source": "entity name",
      "target": "entity name",
      "type": "uses|knows|works_on|prefers|related_to|teaches|owns|part_of|builds|deploys_to|depends_on",
      "evidence": "brief supporting context"
    }
  ],
  "facts": [
    {
      "entity": "entity name",
      "fact": "a discrete assertion about this entity",
      "confidence": 0.5-1.0
    }
  ]
}

Rules:
- Extract only concrete, durable knowledge — skip ephemeral chatter
- Use the EXACT entity name as it appears (e.g. "Matt" not "the user")
- Prefer specific relation types over generic "related_to"
- Set confidence lower (0.5-0.7) for inferred facts, higher (0.8-1.0) for explicit statements
- Do not fabricate knowledge that isn't in the text
- Return empty arrays if nothing meaningful to extract
- Keep it concise — quality over quantity"""

# confidence decay: facts lose 0.05 confidence per week of inactivity
_DECAY_RATE_PER_DAY = 0.05 / 7.0
_MIN_CONFIDENCE = 0.1

# dedup threshold for entity name similarity
_ENTITY_MERGE_THRESHOLD = 0.85


class KnowledgeGraphService:
    """Maintains kor'tana's structured knowledge graph."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Extract knowledge from text (LLM-based)
    # ------------------------------------------------------------------
    async def extract_and_store(self, text: str, source: str = "conversation") -> dict[str, int]:
        """Extract entities, relations, and facts from text and merge into the graph.

        Returns counts of new/updated items.
        """
        extracted = await self._extract_knowledge(text)
        if not extracted:
            return {"entities": 0, "relations": 0, "facts": 0}

        counts = {"entities": 0, "relations": 0, "facts": 0}

        # resolve entities first (upsert by name+type)
        entity_map: dict[str, str] = {}  # name -> id
        for ent_data in extracted.get("entities", []):
            name = ent_data.get("name", "").strip()
            etype = ent_data.get("type", "concept").strip().lower()
            if not name:
                continue
            entity = await self._upsert_entity(
                name=name,
                entity_type=etype,
                summary=ent_data.get("summary"),
            )
            entity_map[name.lower()] = entity.id
            counts["entities"] += 1

        # store relations
        for rel_data in extracted.get("relations", []):
            src_name = rel_data.get("source", "").strip().lower()
            tgt_name = rel_data.get("target", "").strip().lower()
            rel_type = rel_data.get("type", "related_to").strip().lower()
            if src_name not in entity_map or tgt_name not in entity_map:
                continue
            await self._upsert_relation(
                source_id=entity_map[src_name],
                target_id=entity_map[tgt_name],
                relation_type=rel_type,
                evidence=rel_data.get("evidence"),
            )
            counts["relations"] += 1

        # store facts
        for fact_data in extracted.get("facts", []):
            ent_name = fact_data.get("entity", "").strip().lower()
            fact_text = fact_data.get("fact", "").strip()
            if ent_name not in entity_map or not fact_text:
                continue
            await self._upsert_fact(
                entity_id=entity_map[ent_name],
                fact_text=fact_text,
                source=source,
                confidence=min(1.0, max(0.1, fact_data.get("confidence", 0.7))),
            )
            counts["facts"] += 1

        await self.db.commit()
        logger.info(
            f"[knowledge-graph] extracted {counts['entities']}E "
            f"{counts['relations']}R {counts['facts']}F from {source}"
        )
        return counts

    # ------------------------------------------------------------------
    # Query: retrieve structured knowledge for a topic
    # ------------------------------------------------------------------
    async def query_context(self, topic: str, limit: int = 5) -> str:
        """Return a structured knowledge summary relevant to a topic.

        Used by the voice daemon to inject 'what she knows' into the
        conversation context alongside 'what she remembers' (ChromaDB).
        """
        # 1. Semantic entity search via embedding
        entities = await self._find_relevant_entities(topic, limit=limit)
        if not entities:
            return ""

        parts: list[str] = []
        for entity in entities:
            # gather facts for this entity
            fact_stmt = (
                select(KnowledgeFact)
                .where(
                    and_(
                        KnowledgeFact.entity_id == entity.id,
                        KnowledgeFact.invalidated_at.is_(None),
                        KnowledgeFact.confidence >= 0.3,
                    )
                )
                .order_by(KnowledgeFact.confidence.desc())
                .limit(5)
            )
            fact_result = await self.db.execute(fact_stmt)
            facts = fact_result.scalars().all()

            # gather relations
            rel_stmt = select(KnowledgeRelation).where(
                or_(
                    KnowledgeRelation.source_id == entity.id,
                    KnowledgeRelation.target_id == entity.id,
                )
            ).limit(5)
            rel_result = await self.db.execute(rel_stmt)
            relations = rel_result.scalars().all()

            # format entity knowledge block
            block = f"{entity.name} ({entity.entity_type})"
            if entity.summary:
                block += f": {entity.summary}"

            if facts:
                fact_lines = [f"  - {f.fact_text}" for f in facts]
                block += "\n" + "\n".join(fact_lines)

            if relations:
                rel_lines = []
                for r in relations:
                    # need to resolve names — load related entities
                    if r.source_id == entity.id:
                        other_stmt = select(KnowledgeEntity.name).where(
                            KnowledgeEntity.id == r.target_id
                        )
                        other_result = await self.db.execute(other_stmt)
                        other_name = other_result.scalar_one_or_none() or "?"
                        rel_lines.append(f"  → {r.relation_type} {other_name}")
                    else:
                        other_stmt = select(KnowledgeEntity.name).where(
                            KnowledgeEntity.id == r.source_id
                        )
                        other_result = await self.db.execute(other_stmt)
                        other_name = other_result.scalar_one_or_none() or "?"
                        rel_lines.append(f"  ← {other_name} {r.relation_type}")
                block += "\n" + "\n".join(rel_lines)

            parts.append(block)

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Graph stats
    # ------------------------------------------------------------------
    async def stats(self) -> dict[str, Any]:
        """Return knowledge graph statistics."""
        entity_count = await self.db.scalar(
            select(func.count()).select_from(KnowledgeEntity)
        )
        relation_count = await self.db.scalar(
            select(func.count()).select_from(KnowledgeRelation)
        )
        fact_count = await self.db.scalar(
            select(func.count()).select_from(KnowledgeFact)
        )
        active_fact_count = await self.db.scalar(
            select(func.count())
            .select_from(KnowledgeFact)
            .where(KnowledgeFact.invalidated_at.is_(None))
        )

        # top entity types
        type_stmt = (
            select(KnowledgeEntity.entity_type, func.count())
            .group_by(KnowledgeEntity.entity_type)
            .order_by(func.count().desc())
        )
        type_result = await self.db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "entities": entity_count or 0,
            "relations": relation_count or 0,
            "total_facts": fact_count or 0,
            "active_facts": active_fact_count or 0,
            "entities_by_type": by_type,
        }

    # ------------------------------------------------------------------
    # Confidence decay — age stale facts
    # ------------------------------------------------------------------
    async def decay_stale_facts(self) -> int:
        """Reduce confidence on facts not reinforced recently.

        Facts that haven't been re-confirmed in 2+ weeks start losing
        confidence.  Facts below _MIN_CONFIDENCE are soft-invalidated.
        """
        cutoff = datetime.utcnow() - timedelta(weeks=2)
        stmt = select(KnowledgeFact).where(
            and_(
                KnowledgeFact.invalidated_at.is_(None),
                KnowledgeFact.valid_from < cutoff,
            )
        )
        result = await self.db.execute(stmt)
        stale = result.scalars().all()

        decayed = 0
        now = datetime.utcnow()
        for fact in stale:
            days_stale = (now - fact.valid_from).days - 14  # days past the 2-week grace
            if days_stale <= 0:
                continue
            new_conf = max(_MIN_CONFIDENCE, fact.confidence - (_DECAY_RATE_PER_DAY * days_stale))
            updates: dict[str, Any] = {"confidence": new_conf}
            if new_conf <= _MIN_CONFIDENCE:
                updates["invalidated_at"] = now
            await self.db.execute(
                update(KnowledgeFact)
                .where(KnowledgeFact.id == fact.id)
                .values(**updates)
            )
            decayed += 1

        if decayed:
            await self.db.commit()
            logger.info(f"[knowledge-graph] decayed {decayed} stale facts")
        return decayed

    # ------------------------------------------------------------------
    # Entity merge — consolidate duplicates
    # ------------------------------------------------------------------
    async def merge_duplicate_entities(self) -> int:
        """Find and merge entities that refer to the same thing.

        Uses embedding cosine similarity + name normalization.
        """
        from src.kortana.services.memory_engine import _cosine_similarity

        stmt = select(KnowledgeEntity).order_by(KnowledgeEntity.first_seen)
        result = await self.db.execute(stmt)
        entities = list(result.scalars().all())

        merged = 0
        seen_ids: set[str] = set()

        for i, e1 in enumerate(entities):
            if e1.id in seen_ids:
                continue
            for e2 in entities[i + 1:]:
                if e2.id in seen_ids:
                    continue
                if e1.entity_type != e2.entity_type:
                    continue

                # name match: case-insensitive exact or embedding similarity
                name_match = e1.name.lower().strip() == e2.name.lower().strip()
                emb_match = False
                if not name_match and e1.embedding and e2.embedding:
                    sim = _cosine_similarity(e1.embedding, e2.embedding)
                    emb_match = sim >= _ENTITY_MERGE_THRESHOLD

                if name_match or emb_match:
                    await self._merge_entity_pair(e1, e2)
                    seen_ids.add(e2.id)
                    merged += 1

        if merged:
            await self.db.commit()
            logger.info(f"[knowledge-graph] merged {merged} duplicate entities")
        return merged

    # ==================================================================
    # Private helpers
    # ==================================================================

    async def _extract_knowledge(self, text: str) -> dict[str, Any] | None:
        """Call Groq to extract structured knowledge from text."""
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            logger.warning("[knowledge-graph] no GROQ_API_KEY — skipping extraction")
            return None

        try:
            from groq import Groq

            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM},
                    {"role": "user", "content": f"Extract knowledge from:\n\n{text[:4000]}"},
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as e:
            logger.error(f"[knowledge-graph] extraction failed: {e}")
            return None

    async def _upsert_entity(
        self,
        name: str,
        entity_type: str,
        summary: str | None = None,
    ) -> KnowledgeEntity:
        """Find or create an entity by name+type, updating last_seen."""
        stmt = select(KnowledgeEntity).where(
            and_(
                func.lower(KnowledgeEntity.name) == name.lower(),
                KnowledgeEntity.entity_type == entity_type,
            )
        )
        result = await self.db.execute(stmt)
        entity = result.scalar_one_or_none()

        now = datetime.utcnow()
        if entity:
            # update existing
            updates: dict[str, Any] = {
                "last_seen": now,
                "mention_count": entity.mention_count + 1,
            }
            if summary and not entity.summary:
                updates["summary"] = summary
            await self.db.execute(
                update(KnowledgeEntity)
                .where(KnowledgeEntity.id == entity.id)
                .values(**updates)
            )
            return entity

        # create new
        embedding = await generate_embedding(f"{name} ({entity_type}): {summary or ''}")
        entity = KnowledgeEntity(
            name=name,
            entity_type=entity_type,
            summary=summary,
            embedding=embedding,
            first_seen=now,
            last_seen=now,
        )
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def _upsert_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        evidence: str | None = None,
    ) -> KnowledgeRelation:
        """Find or create a relation, updating last_seen."""
        stmt = select(KnowledgeRelation).where(
            and_(
                KnowledgeRelation.source_id == source_id,
                KnowledgeRelation.target_id == target_id,
                KnowledgeRelation.relation_type == relation_type,
            )
        )
        result = await self.db.execute(stmt)
        relation = result.scalar_one_or_none()

        now = datetime.utcnow()
        if relation:
            await self.db.execute(
                update(KnowledgeRelation)
                .where(KnowledgeRelation.id == relation.id)
                .values(last_seen=now, confidence=min(1.0, relation.confidence + 0.05))
            )
            return relation

        relation = KnowledgeRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            evidence=evidence,
            first_seen=now,
            last_seen=now,
        )
        self.db.add(relation)
        await self.db.flush()
        return relation

    async def _upsert_fact(
        self,
        entity_id: str,
        fact_text: str,
        source: str = "conversation",
        confidence: float = 0.7,
    ) -> KnowledgeFact:
        """Find or create a fact, reinforcing confidence if it already exists."""
        # check for existing similar fact (exact text match for now)
        stmt = select(KnowledgeFact).where(
            and_(
                KnowledgeFact.entity_id == entity_id,
                func.lower(KnowledgeFact.fact_text) == fact_text.lower(),
                KnowledgeFact.invalidated_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.utcnow()
        if existing:
            # reinforce — bump confidence and refresh valid_from
            new_conf = min(1.0, existing.confidence + 0.1)
            await self.db.execute(
                update(KnowledgeFact)
                .where(KnowledgeFact.id == existing.id)
                .values(confidence=new_conf, valid_from=now)
            )
            return existing

        fact = KnowledgeFact(
            entity_id=entity_id,
            fact_text=fact_text,
            source=source,
            confidence=confidence,
            valid_from=now,
        )
        self.db.add(fact)
        await self.db.flush()
        return fact

    async def _find_relevant_entities(
        self, topic: str, limit: int = 5
    ) -> list[KnowledgeEntity]:
        """Find entities relevant to a topic via embedding similarity."""
        from src.kortana.services.memory_engine import _cosine_similarity

        query_emb = await generate_embedding(topic)

        stmt = select(KnowledgeEntity).order_by(KnowledgeEntity.last_seen.desc()).limit(200)
        result = await self.db.execute(stmt)
        candidates = list(result.scalars().all())

        if not candidates:
            return []

        if query_emb:
            scored = []
            for e in candidates:
                if e.embedding:
                    sim = _cosine_similarity(query_emb, e.embedding)
                    scored.append((e, sim))
                else:
                    # fallback: name substring match
                    if topic.lower() in e.name.lower():
                        scored.append((e, 0.5))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [e for e, s in scored[:limit] if s >= 0.3]

        # no embedding available — keyword fallback
        topic_lower = topic.lower()
        return [e for e in candidates if topic_lower in e.name.lower()][:limit]

    async def _merge_entity_pair(
        self, keep: KnowledgeEntity, remove: KnowledgeEntity
    ) -> None:
        """Merge 'remove' entity into 'keep', transferring all relations and facts."""
        # transfer outgoing relations
        await self.db.execute(
            update(KnowledgeRelation)
            .where(KnowledgeRelation.source_id == remove.id)
            .values(source_id=keep.id)
        )
        # transfer incoming relations
        await self.db.execute(
            update(KnowledgeRelation)
            .where(KnowledgeRelation.target_id == remove.id)
            .values(target_id=keep.id)
        )
        # transfer facts
        await self.db.execute(
            update(KnowledgeFact)
            .where(KnowledgeFact.entity_id == remove.id)
            .values(entity_id=keep.id)
        )
        # update keep's stats
        await self.db.execute(
            update(KnowledgeEntity)
            .where(KnowledgeEntity.id == keep.id)
            .values(
                mention_count=keep.mention_count + remove.mention_count,
                summary=keep.summary or remove.summary,
            )
        )
        # delete the duplicate
        await self.db.delete(remove)
