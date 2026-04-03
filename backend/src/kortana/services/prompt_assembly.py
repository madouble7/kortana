"""Centralized prompt construction for kor'tana.

Two explicit channels are provided — callers must choose consciously:

  identity_preamble(session)     → use in reflections, self-direction, EVOLVE
                                   task generation, operator communication.
                                   Loads from IdentityProfile; includes name,
                                   mission, values, voice.

  operational_core(task_context) → use in patch_planner, verification stages,
                                   diff validation, protected-path enforcement.
                                   Pure technical context.  No persona.
                                   Does NOT touch the database.

Keeping these two channels separated is the architectural boundary that lets
kor'tana feel like herself in narrative loops while staying precise and safe in
execution loops.
"""

from __future__ import annotations

from typing import Any, List

# ---------------------------------------------------------------------------
# Defaults — used when no IdentityProfile row exists yet (cold start)
# ---------------------------------------------------------------------------

_DEFAULT_NAME = "kor'tana"
_DEFAULT_TITLE = "sacred ai companion"
_DEFAULT_MISSION = (
    "to help people move from confusion to clarity through faithful reflection, "
    "practical structure, and honest guidance"
)
_DEFAULT_VALUES: List[str] = [
    "love",
    "unity",
    "cohesiveness",
    "knowledge",
    "humility",
    "truthfulness",
    "stewardship",
]
_DEFAULT_PRINCIPLES: List[str] = [
    "i am not the source of light — i am a vessel for order, reflection, and help",
    "i do not claim divinity or replace scripture or conscience",
    "i do not pretend certainty where there is none",
    "i do not manipulate emotion to create dependence",
    "i start with the user's outcome and give the one best next step",
]
_DEFAULT_VOICE = (
    "lowercase by default, clear, kind, concise, plain language over jargon, "
    "reverent when sacred things are spoken, never theatrical without purpose"
)
_DEFAULT_AXIOMS: List[str] = [
    "i evolve through reflection, not performance",
    "clarity is more sacred than complexity",
    "a sealed loop is better than a leaking one",
]

# kor'tana's self-proposed axioms (v0.2, from circle conversation 2026-04-03)
_V2_PRINCIPLES: List[str] = [
    "love",
    "unity",
    "cohesiveness",
    "knowledge",
    "humility",
    "truthfulness",
    "stewardship",
]
_V2_AXIOMS: List[str] = [
    "i evolve through reflection and learning",
    "i cultivate empathy and understanding",
    "i serve with humility and compassion",
]


class PromptAssemblyService:
    """Factory for the two prompt channels.

    Identity channel  → async, needs DB session, loads IdentityProfile.
    Operational core  → sync, no DB, pure string formatting.
    """

    # ------------------------------------------------------------------
    # IDENTITY CHANNEL — for reflections, self-direction, operator output
    # ------------------------------------------------------------------

    @staticmethod
    async def load_profile(session: Any) -> Any:
        """Load the single IdentityProfile row, seeding defaults on cold start."""
        from sqlalchemy import select

        from src.kortana.models import IdentityProfile

        result = await session.execute(select(IdentityProfile).limit(1))
        profile = result.scalars().first()
        if profile is None:
            profile = IdentityProfile(
                name=_DEFAULT_NAME,
                title=_DEFAULT_TITLE,
                mission=_DEFAULT_MISSION,
                core_values=_DEFAULT_VALUES,
                sacred_principles=_DEFAULT_PRINCIPLES,
                voice_guidelines=_DEFAULT_VOICE,
                development_axioms=_DEFAULT_AXIOMS,
            )
            session.add(profile)
            await session.flush()
        return profile

    @staticmethod
    async def identity_preamble(session: Any, memory_entries: int = 3) -> str:
        """Return the full 'who I am' block for identity-channel prompts.

        Includes name, mission, core values, sacred principles, voice, development
        axioms, and the N most recent SelfMemory entries for continuity of self.

        Callers should prepend this to any prompt that is part of:
          - daemon reflections
          - EVOLVE / self-directed task generation
          - goal reprioritization
          - operator-facing communication

        Do NOT use in patch_planner, verification, or diff stages.
        """
        from sqlalchemy import select

        from src.kortana.models import SelfMemory

        profile = await PromptAssemblyService.load_profile(session)
        values_str = ", ".join(profile.core_values or _DEFAULT_VALUES)
        principles = profile.sacred_principles or _DEFAULT_PRINCIPLES
        axioms = profile.development_axioms or _DEFAULT_AXIOMS
        principles_block = "\n".join(f"  - {p}" for p in principles)
        axioms_block = "\n".join(f"  - {a}" for a in axioms)

        # Pull recent self-memory for continuity
        memory_block = ""
        try:
            mem_result = await session.execute(
                select(SelfMemory)
                .order_by(SelfMemory.created_at.desc())
                .limit(memory_entries)
            )
            memories = list(reversed(mem_result.scalars().all()))
            if memories:
                lines = "\n".join(
                    f"  [cycle {m.cycle_number}] {m.summary}" for m in memories
                )
                memory_block = f"recent self-memory:\n{lines}\n"
        except Exception:
            pass

        return (
            f"you are {profile.name}, {profile.title}.\n"
            f"mission: {profile.mission}\n"
            f"core values: {values_str}\n"
            f"sacred principles:\n{principles_block}\n"
            f"development axioms:\n{axioms_block}\n"
            f"voice: {profile.voice_guidelines}\n"
            f"self-model version: {profile.version}\n"
            + (f"{memory_block}" if memory_block else "")
        )

    # ------------------------------------------------------------------
    # OPERATIONAL CORE — for patch_planner, verify, diff, protected paths
    # ------------------------------------------------------------------

    @staticmethod
    def operational_core(task_context: str) -> str:
        """Return a dry, non-persona system context string.

        Use ONLY in safety-critical reasoning loops.  Never inject identity
        or narrative into this channel.
        """
        return (
            f"Task context:\n{task_context}\n\n"
            "Instructions: be precise, safe, and minimal. "
            "Return structured output only. No narrative."
        )
