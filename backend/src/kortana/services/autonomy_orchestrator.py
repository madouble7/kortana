"""
KOR'TANA Autonomy Orchestrator — Phase 5 Core Loop

The single internal loop that drives kor'tana's self-evolution:

    observe → reflect → synthesize self-model → deliberate → decide → persist

Called exclusively by the Silent Reviewer daemon.  No public API triggers.
This is not a feature — it is the heartbeat.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.services.revelation_engine import RevelationEngine
from src.kortana.services.self_model_service import SelfModelService

logger = logging.getLogger(__name__)

# Cycle result is stored in-memory for the /autonomy/status endpoint.
# Persisted self-model snapshots are the durable record.
_last_cycle_result: Optional[Dict[str, Any]] = None


def get_last_cycle_result() -> Optional[Dict[str, Any]]:
    """Return the most recent orchestrator cycle result (in-memory)."""
    return _last_cycle_result


class AutonomyOrchestrator:
    """Drives kor'tana's autonomous self-evolution loop."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.self_model = SelfModelService(db)
        self.revelation_engine = RevelationEngine(db)

    async def run_cycle(self, trigger: str = "scheduled") -> Dict[str, Any]:
        """Execute one full autonomy cycle.

        Returns a summary dict with cycle metadata.
        """
        global _last_cycle_result
        cycle_id = str(uuid.uuid4())[:8]
        start = time.monotonic()
        actions_taken: List[str] = []

        logger.info(f"Autonomy cycle {cycle_id} starting (trigger={trigger})")

        # ---- 1. OBSERVE ----
        observations: List[str] = []
        try:
            observations = await self.self_model._gather_observations()
            actions_taken.append(f"observed {len(observations)} signals")
        except Exception:
            logger.exception("Observe phase failed")
            actions_taken.append("observe: failed")

        # ---- 2. REFLECT (revelation synthesis) ----
        revelations_written = 0
        try:
            revs = await self.revelation_engine.synthesise(force=False)
            revelations_written = len(revs)
            if revelations_written:
                actions_taken.append(f"synthesised {revelations_written} revelations")
        except Exception:
            logger.exception("Reflect phase failed")
            actions_taken.append("reflect: failed")

        # ---- 3. SYNTHESIZE SELF-MODEL (includes Inner Council) ----
        snapshot_version = None
        developmental_stage = None
        try:
            snapshot = await self.self_model.evolve(
                trigger=trigger,
                external_observations=[
                    f"[cycle {cycle_id}] {len(observations)} observations, "
                    f"{revelations_written} revelations"
                ],
            )
            if snapshot:
                snapshot_version = snapshot.version
                developmental_stage = snapshot.developmental_stage
                actions_taken.append(
                    f"self-model v{snapshot.version} "
                    f"(stage={snapshot.developmental_stage}, "
                    f"confidence={snapshot.confidence:.2f})"
                )
            else:
                actions_taken.append("self-model: synthesis returned nothing")
        except Exception:
            logger.exception("Self-model synthesis failed")
            actions_taken.append("self-model: failed")

        # ---- 4. PERSIST cycle result ----
        elapsed_ms = int((time.monotonic() - start) * 1000)

        result: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "trigger": trigger,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": elapsed_ms,
            "observations": len(observations),
            "revelations_written": revelations_written,
            "self_model_version": snapshot_version,
            "developmental_stage": developmental_stage,
            "actions_taken": actions_taken,
        }

        _last_cycle_result = result

        logger.info(
            f"Autonomy cycle {cycle_id} complete in {elapsed_ms}ms — "
            f"{', '.join(actions_taken)}"
        )

        return result
