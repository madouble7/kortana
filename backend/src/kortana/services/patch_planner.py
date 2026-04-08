import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional, cast

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import IncidentMemory, RepairPlaybook
from src.kortana.services.gemini import GeminiService
from src.kortana.services.memory_policy import MemoryPolicyService, MemorySurface
from src.kortana.services.patch_validator import PatchValidator, ValidationFailure

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

    def __init__(self, worktree_dir: str, db_session: Optional[AsyncSession] = None):
        self.worktree_dir = worktree_dir
        self.gemini = GeminiService()
        self._db: Optional[AsyncSession] = db_session

    async def _query_ai(
        self,
        prompt: str,
        system_instruction: str,
        mode: str = "best",
        json_mode: bool = False,
    ) -> str:
        """Query AI with Gemini-first routing and shared backoff+fallback.

        Checks the shared provider backoff dict from GitHubAutonomyService.
        If Gemini is in backoff, goes directly to the consensus engine.
        If Gemini returns a quota response, records backoff and falls back.
        """
        from src.kortana.services.ai_consensus import (
            ConsensusMode,
            get_consensus_engine,
        )
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        now = datetime.utcnow()
        gemini_backoff_until = GitHubAutonomyService._provider_backoff_until.get(
            "gemini"
        )
        gemini_available = not (gemini_backoff_until and gemini_backoff_until > now)

        if gemini_available:
            try:
                response = await self.gemini.analyze_text(
                    prompt, system_instruction=system_instruction, json_mode=json_mode
                )
                if GitHubAutonomyService._is_gemini_quota_response(response):
                    GitHubAutonomyService._provider_backoff_until["gemini"] = (
                        datetime.utcnow()
                        + timedelta(
                            seconds=GitHubAutonomyService._provider_backoff_seconds()
                        )
                    )
                    logger.warning(
                        "[PatchPlanner] Gemini quota hit — entering backoff, falling back to consensus"
                    )
                else:
                    return response
            except Exception as exc:
                logger.warning(
                    "[PatchPlanner] Gemini error (%s) — falling back to consensus", exc
                )
        else:
            remaining = (
                int((gemini_backoff_until - now).total_seconds())
                if gemini_backoff_until
                else 0
            )
            logger.info(
                "[PatchPlanner] Gemini in backoff (%ds remaining) — using consensus",
                remaining,
            )

        consensus_mode = ConsensusMode.BEST if mode == "best" else ConsensusMode.FASTEST
        engine = get_consensus_engine()
        result = await engine.query(
            prompt=prompt,
            system=system_instruction,
            mode=consensus_mode,
            max_tokens=2048,
            timeout=30.0,
        )
        if result.providers_succeeded == 0:
            raise RuntimeError("All AI providers failed for patch planner query")
        return result.answer

    def _extract_json(self, response_text: str) -> dict:
        """Extract JSON from potential markdown blocks or prose-wrapped responses.

        Attempts in order:
        1. Raw json.loads on the (fence-stripped) text.
        2. Find first ``{`` … last ``}`` substring (handles prose before/after JSON).
        3. Strip trailing commas before ``}`` / ``]`` (common LLM mistake), retry 1+2.
        4. Raise ValueError so callers can return a safe fallback.
        """

        def _strip_trailing_commas(s: str) -> str:
            return re.sub(r",\s*([}\]])", r"\1", s)

        def _try_loads(s: str) -> dict | None:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return None

        def _try_outermost(s: str) -> dict | None:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                return _try_loads(s[start : end + 1])
            return None

        text = response_text.strip()

        # Step 1: strip markdown fences
        json_match = re.search(
            r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE
        )
        candidate = json_match.group(1).strip() if json_match else text

        # Strategy 1: direct parse
        result = _try_loads(candidate)
        if result is not None:
            return result

        # Strategy 2: outermost { … }
        result = _try_outermost(candidate)
        if result is not None:
            return result

        # Strategy 3: strip trailing commas, then retry strategies 1+2
        cleaned = _strip_trailing_commas(candidate)
        result = _try_loads(cleaned)
        if result is not None:
            return result
        result = _try_outermost(cleaned)
        if result is not None:
            return result

        logger.debug(
            "JSON extraction failed after all strategies. Content: %.120s",
            response_text,
        )
        raise ValueError(f"Malformed JSON in response (length={len(response_text)})")

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

    async def _query_repair_playbook(self, incident_type: str) -> str:
        """Return a formatted string of the top-3 known strategies for this incident type."""
        if self._db is None:
            return ""
        try:
            res = await self._db.execute(
                select(RepairPlaybook)
                .where(
                    RepairPlaybook.incident_type == incident_type,
                    RepairPlaybook.outcome == "success",
                )
                .order_by(RepairPlaybook.times_used.desc())
                .limit(3)
            )
            entries = res.scalars().all()
            if not entries:
                return ""
            lines = ["Known successful repair strategies for this incident type:"]
            for i, entry in enumerate(entries, 1):
                lines.append(
                    f"  {i}. Pattern: {entry.incident_pattern[:120]}\n"
                    f"     Strategy: {entry.chosen_strategy[:200]}\n"
                    f"     Used {entry.times_used} time(s)."
                )
            return "\n".join(lines)
        except Exception as exc:
            logger.warning(f"Could not query RepairPlaybook: {exc}")
            return ""

    async def _write_repair_playbook(
        self,
        incident: IncidentMemory,
        chosen_strategy: str,
        outcome: str,
    ) -> None:
        """Persist a repair outcome to RepairPlaybook for future Stage 1 context."""
        if self._db is None:
            return
        try:
            res = await self._db.execute(
                select(RepairPlaybook)
                .where(
                    RepairPlaybook.incident_type == incident.incident_type,
                    RepairPlaybook.chosen_strategy == chosen_strategy,
                )
                .limit(1)
            )
            existing = cast(Any, res.scalars().first())
            if existing:
                existing.times_used = (existing.times_used or 0) + 1
                existing.last_used_at = datetime.utcnow()
                existing.outcome = outcome
            else:
                entry = RepairPlaybook(
                    id=str(uuid.uuid4()),
                    incident_type=incident.incident_type,
                    incident_pattern=(incident.description or "")[:512],
                    chosen_strategy=chosen_strategy[:1024],
                    outcome=outcome,
                    times_used=1,
                )
                self._db.add(entry)
            await self._db.commit()
        except Exception as exc:
            logger.warning(f"Could not write RepairPlaybook: {exc}")

    def _extract_context_snippets(self, incident: IncidentMemory) -> str:
        """Return file snippets relevant to this incident for Stage 1 context.

        Parses the stack_trace for ``File "path/to/file.py", line N`` patterns,
        reads ±15 lines around each hit that lives inside the worktree, and
        returns a formatted string ready to embed in the Stage 1 prompt.

        At most 3 files × 30 lines are returned to keep the prompt bounded.
        """
        stack_trace = cast(str | None, incident.stack_trace) or ""
        description = cast(str | None, incident.description) or ""

        # Extract file:line references from stack traces
        # Pattern covers both Python tracebacks and pytest output
        file_re = re.compile(
            r'File "([^"]+)", line (\d+)|([^\s]+\.py):(\d+)', re.MULTILINE
        )

        seen: list[tuple[str, int]] = []
        for m in file_re.finditer(stack_trace + "\n" + description):
            path = m.group(1) or m.group(3)
            lineno = int(m.group(2) or m.group(4))
            if len(seen) >= 3:
                break
            # Normalise: strip leading /app/ or absolute prefixes to get repo-relative path
            for prefix in (
                "/app/",
                self.worktree_dir + os.sep,
                self.worktree_dir + "/",
            ):
                if path.startswith(prefix):
                    path = path[len(prefix) :]
                    break
            seen.append((path, lineno))

        if not seen:
            return ""

        snippets: list[str] = []
        for rel_path, lineno in seen:
            abs_path = os.path.join(self.worktree_dir, rel_path)
            if not os.path.isfile(abs_path):
                logger.debug(
                    "_extract_context_snippets: path not found in worktree: %s — "
                    "injecting unavailable sentinel",
                    abs_path,
                )
                snippets.append(
                    f"# {rel_path}\n"
                    "// [Context Unavailable: worktree path could not be resolved.]\n"
                )
                continue
            try:
                with open(abs_path, encoding="utf-8", errors="replace") as fh:
                    all_lines = fh.readlines()
                start = max(0, lineno - 16)
                end = min(len(all_lines), lineno + 15)
                excerpt = "".join(all_lines[start:end])
                snippets.append(
                    f"# {rel_path} (lines {start + 1}–{end})\n```python\n{excerpt}\n```"
                )
            except OSError as exc:
                logger.debug(
                    "_extract_context_snippets: could not read %s (%s) — "
                    "injecting unavailable sentinel",
                    abs_path,
                    exc,
                )
                snippets.append(
                    f"# {rel_path}\n"
                    "// [Context Unavailable: OSError reading worktree path — "
                    f"{exc}]\n"
                )

        return "\n\n".join(snippets)

    async def _load_patch_analysis_context(self, incident: IncidentMemory) -> str:
        """Return bounded non-persona memory for Stage 1 incident analysis."""
        if self._db is None:
            return ""

        query = "\n".join(
            part
            for part in (
                str(incident.incident_type or ""),
                str(incident.description or ""),
                str(incident.stack_trace or ""),
            )
            if part
        )
        context = await MemoryPolicyService.build_context(
            self._db,
            surface=MemorySurface.PATCH_ANALYSIS,
            query=query,
            incident=incident,
        )
        return context.render()

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

        playbook_context = await self._query_repair_playbook(
            str(incident.incident_type or "")
        )
        memory_context = await self._load_patch_analysis_context(incident)
        context_snippets = self._extract_context_snippets(incident)
        snippets_section = (
            f"\nCode context around the error:\n{context_snippets}\n"
            if context_snippets
            else ""
        )
        memory_section = (
            f"\nDurable reasoning memory:\n{memory_context}\n"
            if memory_context
            else ""
        )
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
{snippets_section}
{memory_section}
{playbook_context}

Respond with JSON only."""

        try:
            response = await self._query_ai(
                prompt, system_instruction, mode="best", json_mode=True
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
            response = await self._query_ai(prompt, system_instruction, mode="best")
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
            with open(temp_patch_path, "w", encoding="utf-8", newline="\n") as f:
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
            response = await self._query_ai(
                prompt, system_instruction, mode="fastest", json_mode=True
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

            # Guardrail: validate diff before touching the worktree
            context_snippets = self._extract_context_snippets(incident)
            validator = PatchValidator(self.worktree_dir)
            validation = validator.validate(diff, context_snippets)
            if isinstance(validation, ValidationFailure):
                logger.warning(
                    "PatchValidator rejected diff for incident %s: %s",
                    incident.id,
                    validation.summary(),
                )
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
                incident.fix_status = "validation_failed"  # type: ignore[assignment]
                incident.resolution_strategy = f"Auto-heal validation failed in Stage 3.\n\nRisk: {verification.residual_risk}\nRuff Output:\n{ruff_output}\n\nPytest Output:\n{pytest_output}"  # type: ignore[assignment]
                await self._write_repair_playbook(
                    incident,
                    chosen_strategy=str(plan.root_cause),
                    outcome="failure",
                )
                return False

            logger.info(
                f"Patch applied successfully. Summary: {verification.pr_summary}"
            )
            incident.resolution_strategy = f"Auto-heal patch verified successfully.\n\nSummary: {verification.pr_summary}\nRuff Output:\n{ruff_output}\n\nPytest Output:\n{pytest_output}"  # type: ignore[assignment]
            await self._write_repair_playbook(
                incident,
                chosen_strategy=str(plan.root_cause),
                outcome="success",
            )
            return True

        except Exception as e:
            logger.error(f"PatchPlanner: Pipeline failed: {e}")
            return False
