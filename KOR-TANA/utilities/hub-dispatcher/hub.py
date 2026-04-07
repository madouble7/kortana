import asyncio
import logging
from typing import Any, Dict

from .persona import Persona
from .skill_base import Skill


class Hub:
    """Central hub that holds a persona and a registry of skills."""

    def __init__(self, persona: Persona | None = None):
        logging.basicConfig(level=logging.INFO)
        self.persona = persona or Persona()
        self._skills: list[Skill] = []
        self.input_queue: asyncio.Queue[Any] = asyncio.Queue()

    def register(self, skill: Skill) -> None:
        """Register a Skill instance with the hub."""
        self._skills.append(skill)

    def dispatch(self, intent: Any, context: Dict[str, Any] | None = None) -> str:
        """Dispatch an intent to a skill.

        intent may be:
        - a string intent name, or
        - a tuple (name, data)
        """
        context = context or {}

        if isinstance(intent, tuple) and len(intent) >= 1:
            name = intent[0]
            data = intent[1] if len(intent) > 1 else {}
        elif isinstance(intent, str):
            name = intent
            data = {}
        else:
            # unknown shape
            name = str(intent)
            data = {}

        name = name.lower()

        for skill in self._skills:
            try:
                if skill.can_handle(name, data):
                    return skill.handle(name, data)
            except Exception:
                # Skill raised an error; continue to next skill
                continue

        # Fallback response
        return self.persona.speak("Sorry — I don't know how to handle that.")

    async def process_intents(self):
        """Asynchronously process intents from the input queue in parallel."""
        while True:
            intent = await self.input_queue.get()
            try:
                # Spawn each intent as a separate concurrent task for parallel evolution
                asyncio.create_task(self.handle_intent_concurrently(intent))
                self.input_queue.task_done()
            except Exception as e:
                print(f"Error spawning intent {intent}: {e}")

    async def handle_intent_concurrently(self, intent: Any):
        """Handles a single intent concurrently with others."""
        try:
            # We use to_thread for synchronous dispatch if skills are blocking
            # or await if dispatch/handle were converted to async
            response = self.dispatch(intent)
            # Log results for the evolution lineage
            logging.info(f"Parallel Evolution Result [{intent}]: {response}")
        except Exception as e:
            logging.error(f"Failed parallel intent {intent}: {e}")
