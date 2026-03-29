import logging
import os

from src.kortana.models import IncidentMemory

logger = logging.getLogger(__name__)


class PatchPlanner:
    """
    Patch Planner stub for Vector Alpha.
    This reads an incident and mutates files ONLY within the isolated worktree.
    Later, this class will use an LLM (Gemini/Beta) to formulate and apply diffs.
    """

    def __init__(self, worktree_dir: str):
        self.worktree_dir = worktree_dir

    async def apply_healing_patch(self, incident: IncidentMemory) -> bool:
        """
        Synthesize and apply a patch.
        For now, this is a placeholder that does a simple mock file edit
        to prove the pipeline works in the isolated worktree.
        """
        logger.info(
            f"PatchPlanner: Analyzing incident {incident.id} ({incident.incident_type})"
        )

        try:
            # Demonstration patch logic: create a repair log inside the worktree
            # This proves we have write access to the correct isolated location
            # and that it will be captured by `git add -u` (if tracked) or we can just touch a known file

            # Let's touch a known file that we can safely modify, e.g. a self_healing log
            # We will just append a comment to an existing file or write to a dummy file.
            # To ensure `git add -u` picks it up, we can append a blank line to backend/README.md or similar
            # For safety, let's just create/append to backend/VECTOR_ALPHA_STAMP.txt
            # For safety, let's just append to backend/pytest.ini inside the worktree
            target_file = os.path.join(self.worktree_dir, "backend", "pytest.ini")
            if os.path.exists(target_file):
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(f"\n# Vector Alpha Auto-Patch for incident {incident.id}\n")
                logger.info("PatchPlanner: Applied dummy patch to backend/pytest.ini")
                return True

            return False
        except Exception as e:
            logger.error(f"PatchPlanner: Failed to apply patch: {e}")
            return False
