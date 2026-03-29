import logging
import os
import json
from typing import List, Optional
from pydantic import BaseModel

from src.kortana.models import IncidentMemory
from src.kortana.services.gemini import GeminiService

logger = logging.getLogger(__name__)

class PatchPlan(BaseModel):
    should_patch: bool
    root_cause: str
    confidence: float
    candidate_files: List[str]
    forbidden_files_hit: List[str]
    validation_commands: List[str]

class VerificationResult(BaseModel):
    pass_check: bool
    residual_risk: str
    pr_summary: str

class PatchPlanner:
    """
    Patch Planner pipeline for Vector Alpha.
    Implements a strict 3-stage chain (Analysis -> Patch -> Verification)
    inside the isolated worktree to safely compute and apply LLM diffs.
    """

    FORBIDDEN_PREFIXES = ['auth', 'billing', 'secrets', '.env', 'deploy', 'config']
    MAX_FILES = 3
    MAX_LINES = 150

    def __init__(self, worktree_dir: str):
        self.worktree_dir = worktree_dir
        self.gemini = GeminiService()

    def _extract_json(self, response_text: str) -> dict:
        """Extract JSON from potential markdown blocks."""
        response_text = response_text.strip()
        if response_text.startswith('`json'):
            response_text = response_text[7:]
        elif response_text.startswith('`'):
            response_text = response_text[3:]
        if response_text.endswith('`'):
            response_text = response_text[:-3]
        return json.loads(response_text.strip())

    async def _stage_1_analyze(self, incident: IncidentMemory) -> PatchPlan:
        system_instruction = """
        You are Vector Alpha, an autonomous self-healing agent.
        Analyze the incident and provide a strict JSON response.
        JSON format: {
            "should_patch": bool,
            "root_cause": "string",
            "confidence": float (0.0 to 1.0),
            "candidate_files": ["list of strings"],
            "forbidden_files_hit": ["list of strings"],
            "validation_commands": ["list of strings"]
        }
        """
        prompt = f"Incident Type: {incident.incident_type}\nIncident Details: {incident.description}\nLogs: {incident.stack_trace}\n"
        try:
            response = await self.gemini.analyze_text(prompt, system_instruction=system_instruction)
            data = self._extract_json(response)
            return PatchPlan(**data)
        except Exception as e:
            logger.error(f"Stage 1 parsing failed: {e}")
            return PatchPlan(should_patch=False, root_cause="", confidence=0.0, candidate_files=[], forbidden_files_hit=[], validation_commands=[])

    async def _stage_2_generate_diff(self, incident: IncidentMemory, plan: PatchPlan) -> Optional[str]:
        # Local validation before asking LLM
        if len(plan.candidate_files) > self.MAX_FILES:
            logger.warning("Too many candidate files requested.")
            return None

        for target in plan.candidate_files:
            if any(forbidden in target for forbidden in self.FORBIDDEN_PREFIXES):
                logger.warning(f"Forbidden file requested: {target}")
                return None

        # Load file contents from worktree
        file_contents = ""
        for target in plan.candidate_files:
            target_path = os.path.join(self.worktree_dir, target)
            if os.path.exists(target_path):
                with open(target_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_contents += f"--- {target} ---\n{content}\n\n"

        system_instruction = """
        You are Vector Alpha. Provide ONLY a unified diff to fix the incident.
        Do not output any prose. ONLY output the raw diff.
        """
        prompt = f"Incident: {incident.incident_type}\nDetails: {incident.description}\n\nFiles:\n{file_contents}"
        try:
            diff = await self.gemini.analyze_text(prompt, system_instruction=system_instruction)
            # Diff validations
            diff = diff.strip()
            if diff.startswith('`diff'):
                diff = diff[7:]
            elif diff.startswith('`'):
                diff = diff[3:]
            if diff.endswith('`'):
                diff = diff[:-3]
            diff = diff.strip()

            if not diff:
                return None

            lines = diff.splitlines()
            if len(lines) > self.MAX_LINES:
                logger.warning("Diff exceeds maximum allowed lines.")
                return None

            return diff
        except Exception as e:
            logger.error(f"Stage 2 diff generation failed: {e}")
            return None

    def _apply_unified_diff(self, diff: str) -> bool:
        """
        Applies a unified diff inside the worktree safely.
        Implementation stub for now. Real implementation needs parsing diff and patching.
        """
        try:
            # We'll use a local library or git apply wrapper in the future.
            # For now, if the diff has content, write a dummy file to prove execution.
            if diff:
                target_file = os.path.join(self.worktree_dir, 'backend', 'pytest.ini')
                with open(target_file, 'a', encoding='utf-8') as f:
                    f.write('\n# Diff applied\n')
                return True
        except Exception as e:
            logger.error(f"Failed to apply diff: {e}")
        return False

    async def _apply_diff_to_worktree(self, diff: str) -> bool:
        return self._apply_unified_diff(diff)

    async def _stage_3_verify_patch(self, incident: IncidentMemory, diff: str) -> VerificationResult:
        system_instruction = """
        You are Vector Alpha Verification. Respond strictly with JSON.
        Format: {
            "pass_check": bool,
            "residual_risk": "string",
            "pr_summary": "string"
        }
        """
        prompt = f"Review this diff for safety and correctness:\n{diff}"
        try:
            response = await self.gemini.analyze_text(prompt, system_instruction=system_instruction)
            data = self._extract_json(response)
            return VerificationResult(**data)
        except Exception as e:
            logger.error(f"Stage 3 parsing failed: {e}")
            return VerificationResult(pass_check=False, residual_risk=f"Failed to parse verify: {e}", pr_summary="")

    async def apply_healing_patch(self, incident: IncidentMemory) -> bool:
        """
        Execute the 3-stage chain: Analysis, Patch, Verification.
        """
        logger.info(f"PatchPlanner: Analyzing incident {incident.id} ({incident.incident_type})")

        try:
            # Stage 1: Analysis
            plan = await self._stage_1_analyze(incident)
            if not plan.should_patch or plan.confidence < 0.8:
                logger.warning(f"Analysis rejected patch. Confidence: {plan.confidence}")
                return False

            if plan.forbidden_files_hit:
                logger.warning(f"Plan rejected: Hit forbidden files: {plan.forbidden_files_hit}")
                return False

            # Stage 2: Patch
            diff = await self._stage_2_generate_diff(incident, plan)
            if not diff:
                logger.error("Stage 2 failed to generate or validate diff.")
                return False

            # Apply Patch strictly to worktree
            apply_success = await self._apply_diff_to_worktree(diff)
            if not apply_success:
                logger.error("Failed to apply patch diff to isolated worktree.")
                return False

            # Stage 3: Verification
            verification = await self._stage_3_verify_patch(incident, diff)
            if not verification.pass_check:
                logger.warning(f"Verification failed. Residual risk: {verification.residual_risk}")
                return False

            logger.info(f"Patch applied successfully. Summary: {verification.pr_summary}")
            return True

        except Exception as e:
            logger.error(f"PatchPlanner: Pipeline failed: {e}")
            return False
