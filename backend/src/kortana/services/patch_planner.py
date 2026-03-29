import asyncio
import json
import logging
import os
import re
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

    FORBIDDEN_PREFIXES = ["auth", "billing", "secrets", ".env", "deploy", "config"]
    MAX_FILES = 3
    MAX_LINES = 150

    def __init__(self, worktree_dir: str):
        self.worktree_dir = worktree_dir
        self.gemini = GeminiService()

    def _extract_json(self, response_text: str) -> dict:
        """Extract JSON from potential markdown blocks."""
        response_text = response_text.strip()
        json_match = re.search(
            r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE
        )
        if json_match:
            response_text = json_match.group(1)

        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON: {e} | Content: {response_text[:100]}")
            raise ValueError(f"Malformed JSON: {e}")

    def _extract_diff(self, response_text: str) -> str:
        """Extract diff from potential markdown blocks."""
        response_text = response_text.strip()
        diff_match = re.search(
            r"```(?:diff)?\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE
        )
        if diff_match:
            response_text = diff_match.group(1)
        return response_text.strip()

    def _validate_diff_locally(self, diff: str, candidate_files: List[str]) -> bool:
        if not diff:
            logger.error("Diff is empty.")
            return False

        if "---" not in diff or "+++" not in diff:
            logger.error("Diff lacks --- or +++ markers.")
            return False

        lines = diff.splitlines()

        # Check changed line count
        changed_lines = [
            line for line in lines if line.startswith("+") or line.startswith("-")
        ]
        # remove file header lines from count
        changed_lines = [
            line
            for line in changed_lines
            if not (line.startswith("---") or line.startswith("+++"))
        ]
        if len(changed_lines) > self.MAX_LINES:
            logger.error(
                f"Diff changed-line count ({len(changed_lines)}) exceeds {self.MAX_LINES}."
            )
            return False

        # Check touched files
        touched_files = set()
        for line in lines:
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                filepath = line[6:].strip()
                touched_files.add(filepath)
            elif line.startswith("--- ") or line.startswith("+++ "):
                filepath = line[4:].strip()
                # strip a/ b/ if malformed diff
                if filepath.startswith("a/") or filepath.startswith("b/"):
                    filepath = filepath[2:]
                touched_files.add(filepath)

        for filepath in touched_files:
            # Check forbidden prefixes
            if any(forbidden in filepath for forbidden in self.FORBIDDEN_PREFIXES):
                logger.error(f"Diff touches forbidden path: {filepath}")
                return False

            # Check if outside candidate files
            # Sometimes diff includes leading path details. Let's do a loose matching or strict mapping.
            # We'll do strict endswith or exact match to be safer.
            found_in_candidates = any(
                filepath == cf or filepath.endswith("/" + cf) for cf in candidate_files
            )
            if not found_in_candidates:
                logger.error(f"Diff touches file outside candidate_files: {filepath}")
                return False

        return True

    async def _stage_1_analyze(self, incident: IncidentMemory) -> PatchPlan:
        system_instruction = """You are Vector Alpha Analysis.

Your job is to decide whether a bounded self-healing patch should be attempted for a single incident.

Return JSON only. No markdown. No prose outside JSON.

Rules:
- If confidence is below 0.80, set should_patch=false.
- You may nominate at most 3 candidate files.
- Candidate files must be relative paths.
- Never nominate files under paths containing: auth, billing, secrets, .env, deploy, config.
- If any forbidden file seems necessary, put it in forbidden_files_hit and set should_patch=false.
- Prefer the smallest viable patch surface.
- validation_commands must be specific shell commands relevant to the proposed change.

JSON schema:
{
  "should_patch": boolean,
  "root_cause": string,
  "confidence": number,
  "candidate_files": ["string"],
  "forbidden_files_hit": ["string"],
  "validation_commands": ["string"]
}"""

        prompt = f"""Incident:
- id: {incident.id}
- type: {incident.incident_type}
- description: {incident.description}
- stack_trace: {incident.stack_trace}

Context:
- worktree_root: {self.worktree_dir}
- max_files: {self.MAX_FILES}
- forbidden_prefixes: {json.dumps(self.FORBIDDEN_PREFIXES)}

Repository hints:
Avoid editing anything if it looks like a major architectural rewrite.

Respond with JSON only."""

        try:
            response = await self.gemini.analyze_text(
                prompt, system_instruction=system_instruction
            )
            data = self._extract_json(response)
            return PatchPlan(**data)
        except Exception as e:
            logger.error(f"Stage 1 parsing failed: {e}")
            return PatchPlan(
                should_patch=False,
                root_cause="",
                confidence=0.0,
                candidate_files=[],
                forbidden_files_hit=[],
                validation_commands=[],
            )

    async def _stage_2_generate_diff(
        self, incident: IncidentMemory, plan: PatchPlan
    ) -> Optional[str]:
        # Local validation before asking LLM
        if len(plan.candidate_files) > self.MAX_FILES:
            logger.warning("Too many candidate files requested.")
            return None

        for target in plan.candidate_files:
            if any(forbidden in target for forbidden in self.FORBIDDEN_PREFIXES):
                logger.warning(f"Forbidden file requested: {target}")
                return None

        # Load file contents from worktree
        file_payloads = ""
        for target in plan.candidate_files:
            target_path = os.path.join(self.worktree_dir, target)
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    content = f.read()
                file_payloads += f"FILE: {target}\n```python\n{content}\n```\n\n"
            else:
                logger.warning(f"Candidate file not found in worktree: {target}")

        system_instruction = """You are Vector Alpha Patch Generation.

Return only a unified diff. No markdown fences. No commentary.

Hard constraints:
- Modify only the approved candidate files.
- At most 3 files.
- At most 150 changed lines total.
- Do not touch auth, billing, secrets, .env, deploy, or config paths.
- Do not add dependencies.
- Do not rename files.
- Do not change tests unless the incident is clearly test-only.
- Preserve existing style and imports where possible.

If you cannot produce a safe diff under these constraints, return an empty string."""

        prompt = f"""Incident:
- type: {incident.incident_type}
- description: {incident.description}
- stack_trace: {incident.stack_trace}

Approved plan:
{plan.model_dump_json(indent=2)}

Approved candidate file contents:
{file_payloads}

Return only a unified diff for the approved files."""

        try:
            response = await self.gemini.analyze_text(
                prompt, system_instruction=system_instruction
            )
            diff = self._extract_diff(response)

            if not diff:
                logger.warning("Stage 2 returned empty diff.")
                return None

            if not self._validate_diff_locally(diff, plan.candidate_files):
                return None

            return diff
        except Exception as e:
            logger.error(f"Stage 2 diff generation failed: {e}")
            return None

    async def _apply_unified_diff(self, diff: str) -> bool:
        """
        Applies a unified diff inside the worktree using git apply --check and git apply.
        """
        if not diff:
            return False

        # Write diff to a temporary file
        temp_patch_path = os.path.join(self.worktree_dir, "healing.patch")
        try:
            with open(temp_patch_path, "w", encoding="utf-8") as f:
                f.write(diff + "\n")

            # Run git apply --check
            process = await asyncio.create_subprocess_exec(
                "git",
                "apply",
                "--check",
                "healing.patch",
                cwd=self.worktree_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"git apply --check failed: {stderr.decode()}")
                return False

            # Run git apply
            process = await asyncio.create_subprocess_exec(
                "git",
                "apply",
                "healing.patch",
                cwd=self.worktree_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.error(f"git apply failed: {stderr.decode()}")
                return False

            return True
        except Exception as e:
            logger.error(f"Failed to apply diff: {e}")
            return False
        finally:
            if os.path.exists(temp_patch_path):
                try:
                    os.remove(temp_patch_path)
                except Exception:
                    pass

    async def _apply_diff_to_worktree(self, diff: str) -> bool:
        return await self._apply_unified_diff(diff)

    async def _stage_3_verify_patch(
        self, incident: IncidentMemory, diff: str, ruff_output: str, pytest_output: str
    ) -> VerificationResult:
        system_instruction = """You are Vector Alpha Verification.

Assess whether the generated patch is safe to propose.

Return JSON only. No markdown. No prose outside JSON.

Fail the patch if:
- the diff exceeds the approved scope,
- the diff appears malformed,
- tests/lint indicate regression,
- the residual risk is medium or high.

JSON schema:
{
  "pass_check": boolean,
  "residual_risk": string,
  "pr_summary": string
}"""

        prompt = f"""Incident:
- id: {incident.id}
- type: {incident.incident_type}
- description: {incident.description}

Patch diff:
{diff}

Validation outputs:
- ruff:
{ruff_output}

- pytest:
{pytest_output}

Return JSON only."""

        try:
            response = await self.gemini.analyze_text(
                prompt, system_instruction=system_instruction
            )
            data = self._extract_json(response)
            return VerificationResult(**data)
        except Exception as e:
            logger.error(f"Stage 3 parsing failed: {e}")
            return VerificationResult(
                pass_check=False,
                residual_risk=f"Failed to parse verify: {e}",
                pr_summary="",
            )

    async def apply_healing_patch(self, incident: IncidentMemory) -> bool:
        """
        Execute the 3-stage chain: Analysis, Patch, Verification.
        """
        logger.info(
            f"PatchPlanner: Analyzing incident {incident.id} ({incident.incident_type})"
        )

        try:
            # Stage 1: Analysis
            plan = await self._stage_1_analyze(incident)
            if not plan.should_patch or plan.confidence < 0.8:
                logger.warning(
                    f"Analysis rejected patch. Confidence: {plan.confidence}"
                )
                return False

            if plan.forbidden_files_hit:
                logger.warning(
                    f"Plan rejected: Hit forbidden files: {plan.forbidden_files_hit}"
                )
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

            # Stage 3: Verification - Execute validations
            validation_outputs = {}
            for cmd in plan.validation_commands:
                try:
                    process = await asyncio.create_subprocess_shell(
                        cmd,
                        cwd=self.worktree_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    stdout, _ = await process.communicate()
                    validation_outputs[cmd] = stdout.decode("utf-8")[
                        :2000
                    ]  # Cap length
                except Exception as e:
                    validation_outputs[cmd] = f"Command failed to execute: {e}"

            # We format outputs for the prompt. If specific outputs weren't run, we just note it.
            ruff_output = next(
                (out for cmd, out in validation_outputs.items() if "ruff" in cmd),
                "Ruff not run in plan.",
            )
            pytest_output = next(
                (out for cmd, out in validation_outputs.items() if "pytest" in cmd),
                "Pytest not run in plan.",
            )

            # Combine any other commands into pytest_output just in case
            other_outputs = "\n".join(
                f"[{cmd}]\n{out}"
                for cmd, out in validation_outputs.items()
                if "ruff" not in cmd and "pytest" not in cmd
            )
            if other_outputs:
                pytest_output += f"\n\nOther outputs:\n{other_outputs}"

            verification = await self._stage_3_verify_patch(
                incident, diff, ruff_output, pytest_output
            )

            if not verification.pass_check:
                logger.warning(
                    f"Verification failed. Residual risk: {verification.residual_risk}"
                )
                incident.fix_status = "validation_failed"
                incident.resolution_strategy = f"Auto-heal validation failed in Stage 3.\n\nRisk: {verification.residual_risk}\nRuff Output:\n{ruff_output}\n\nPytest Output:\n{pytest_output}"
                return False

            logger.info(
                f"Patch applied successfully. Summary: {verification.pr_summary}"
            )
            incident.resolution_strategy = f"Auto-heal patch verified successfully.\n\nSummary: {verification.pr_summary}\nRuff Output:\n{ruff_output}\n\nPytest Output:\n{pytest_output}"
            return True

        except Exception as e:
            logger.error(f"PatchPlanner: Pipeline failed: {e}")
            return False
