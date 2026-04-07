import asyncio
import logging
import random
import threading
from typing import Any, Dict, Optional

from .daemon import load_config
from .hub import Hub
from .memory import MemoryStore
from .model_agent import ModelAgentAdapter
from .skills.creative_skill import CreativeSkill
from .skills.ensemble_arranger_skill import EnsembleArrangerSkill
from .skills.example_skill import ExampleSkill
from .skills.local_watcher_skill import LocalWatcherSkill

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MusicLearningDaemon:
    """Unified MusicLearningDaemon that runs an asyncio loop in a background thread.

    - Creates its own `Hub` and `MemoryStore` when not provided.
    - Registers a small set of safe, local-first skills (ExampleSkill, LocalWatcherSkill,
      CreativeSkill).
    - Uses `ModelAgentAdapter` as a gated adapter (no network unless enabled).

    This class is intentionally conservative: it will not call external services unless
    `allow_network` is set in the config. It writes heartbeats and activity to memory
    so you can audit Kortana's actions.
    """

    def __init__(
        self,
        config_path: str = "kortana_config.json",
        hub: Optional[Hub] = None,
        memory: Optional[MemoryStore] = None,
    ):
        self.config = load_config(config_path)
        self.hub = hub or Hub()
        self.memory = memory or MemoryStore()
        self.knowledge_base: Dict[str, Any] = {
            "genres": set(),
            "artists": set(),
            "trends": [],
            "preferences": {},
        }

        # register safe skills
        self.hub.register(ExampleSkill())
        watch_dir = self.config.get("watch_dir")
        self.hub.register(LocalWatcherSkill(watch_dir=watch_dir))
        self.hub.register(CreativeSkill(outbox_path=self.config.get("outbox_path")))
        self.hub.register(EnsembleArrangerSkill())

        # model adapter (gated)
        self.model_adapter = ModelAgentAdapter(self.config, memory=self.memory)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.logger = logger

    def start(self):
        if self._thread and self._thread.is_alive():
            self.logger.warning("Daemon is already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        self.logger.info("MusicLearningDaemon started.")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self.logger.info("MusicLearningDaemon stopped.")

    def _run_async_loop(self):
        try:
            asyncio.run(self._learning_loop())
        except Exception as e:
            self.logger.error(f"Daemon loop exited with error: {e}")

    async def _learning_loop(self):
        self.logger.info("Starting autonomous learning loop.")
        while not self._stop_event.is_set():
            try:
                await self._fetch_music_trends()
                await self._analyze_user_interactions()
                await self._update_knowledge_base()

                # run local autonomous skills
                for skill in list(self.hub._skills):
                    # call run_periodic if the skill supports it
                    if hasattr(skill, "run_periodic"):
                        try:
                            skill.run_periodic(self.hub, self.memory, self.config)
                        except Exception as e:
                            self.logger.error(
                                f"Error running skill {getattr(skill, 'name', skill)}: {e}"
                            )

                # heartbeat
                try:
                    self.memory.add_note(
                        text="heartbeat", source="music_learning_daemon"
                    )
                except Exception:
                    pass

                await asyncio.sleep(self.config.get("cycle_seconds", 60))
            except Exception as e:
                self.logger.error(f"Error in learning loop: {e}")
                await asyncio.sleep(10)

    async def _fetch_music_trends(self):
        """Mock fetching music trends; only performs simulated network behavior.

        Real network fetches must be implemented separately and gated by `allow_network`.
        """
        await asyncio.sleep(0.5)
        mock_trends = ["pop", "rock", "hip-hop", "electronic", "jazz"]
        trend = random.choice(mock_trends)
        self.logger.info(f"Fetched trend: {trend}")
        await self.hub.input_queue.put(("learned_trend", {"trend": trend}))

    async def _analyze_user_interactions(self):
        music_notes = list(self.memory.search("music", limit=10))
        if music_notes:
            genres = set()
            for note in music_notes:
                text = (note.get("text") or "").lower()
                if "pop" in text:
                    genres.add("pop")
                if "rock" in text:
                    genres.add("rock")
            if genres:
                self.logger.info(f"Analyzed preferences: {genres}")
                await self.hub.input_queue.put(
                    ("learned_preference", {"genres": list(genres)})
                )

    async def _update_knowledge_base(self):
        new_genre = random.choice(["classical", "country", "reggae"])
        self.knowledge_base["genres"].add(new_genre)
        self.logger.info(f"Updated knowledge base: added genre {new_genre}")
        await self.hub.input_queue.put(
            ("knowledge_updated", {"genres": list(self.knowledge_base["genres"])})
        )

    def status(self) -> Dict[str, Any]:
        return {
            "running": self._thread.is_alive() if self._thread else False,
            "memory_path": getattr(self.memory, "path", None),
            "allow_network": bool(self.config.get("allow_network", False)),
        }
