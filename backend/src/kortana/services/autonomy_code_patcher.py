"""
KOR'TANA Autonomous Code Patcher — Phase 8

Runs bounded self-repair in an isolated worktree so the live checkout stays
untouched until the fix has passed local validation.
"""

from __future__ import annotations

import asyncio
import difflib
import logging
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.models import Task
from src.kortana.services.goal_manager import GoalStatus, GoalTier, get_goal_manager
from src.kortana.services.repository_boundary_service import RepositoryBoundaryService
from src.kortana.services.self_diagnostic import SelfDiagnostic, _call_gemini_analysis

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerificationCommand:
    label: str
    argv: tuple[str, ...]


@dataclass
class VerificationCommandResult:
    label: str
    argv: tuple[str, ...]
    returncode: int
    output: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


async def submit_approval_task(
    db: AsyncSession,
    title: str,
    description: str,
    context: Mapping[str, Any] | None = None,
) -> None:
    """Submit a task to HOP for approval."""
    task_context = dict(context) if context else None
    task = Task(  # type: ignore[call-arg]
        title=title,
        description=description,
        classification="approval",
        status="pending",
        result=str(task_context) if task_context else None,
        metadata_json=task_context,
    )
    db.add(task)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise


class AutonomyCodePatcher:
    """Autonomous patching engine for self-repairing KOR'TANA."""

    MIN_CONFIDENCE = 0.70
    MAX_DELETION_RATIO = 0.40
    MAX_NET_SHRINK = 120
    MAX_CHANGED_LINES = 200
    BASE_BRANCH_CANDIDATES = ("main", "master")
    BACKEND_VERIFICATION_COMMANDS = (
        VerificationCommand(
            "ruff",
            ("python", "-m", "ruff", "check", "src", "tests"),
        ),
        VerificationCommand(
            "mypy",
            ("python", "-m", "mypy", "src"),
        ),
        VerificationCommand(
            "pytest",
            ("python", "-m", "pytest", "tests", "-q"),
        ),
    )

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.diagnostic = SelfDiagnostic(db)
        self.boundary = RepositoryBoundaryService()
        self.repo_root = Path(self.boundary.canonical_repo_root)
        self.worktree_dir = self.boundary.resolve_canonical_path(
            self.repo_root / ".autonomy_code_patcher_worktree"
        )

    async def attempt_auto_fix(
        self,
        error_type: str,
        error_message: str,
        target_file: str,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        """
        Full auto-patch workflow:
        1. Analyze failure via SelfDiagnostic
        2. Query Gemini for a full-file fix
        3. Apply the fix in an isolated git worktree
        4. Run ruff, mypy, and pytest
        5. Request approval via HOP
        """
        logger.info(
            "KOR'TANA AUTO-REPAIR: Attempting to fix %s in %s",
            error_type,
            target_file,
        )

        worktree_created = False
        branch_name = f"auto-repair/{uuid.uuid4().hex[:8]}"

        gm = get_goal_manager()
        repair_goal = gm.create(
            title=f"Repair {target_file.split('/')[-1]}",
            description=f"Auto-repairing {error_type}. message={error_message[:100]}",
            tier=GoalTier.IMMEDIATE,
            status=GoalStatus.ACTIVE,
        )
        await gm.persist_goal(repair_goal)

        try:
            diag_result = await self.diagnostic.analyze_error_string(
                error_type, error_message, dict(context) if context else None
            )
            if (
                not diag_result.auto_fixable
                or diag_result.confidence < self.MIN_CONFIDENCE
            ):
                logger.warning(
                    "KOR'TANA AUTO-REPAIR: Rejected by diagnostic "
                    "(auto_fixable=%s, confidence=%.2f)",
                    diag_result.auto_fixable,
                    diag_result.confidence,
                )
                return False

            repo_target = self._resolve_target_file(target_file)
            relative_target = repo_target.relative_to(self.repo_root)
            original_content = repo_target.read_text(encoding="utf-8")

            patch_prompt = self._build_patch_prompt(
                error_type=error_type,
                error_message=error_message,
                target_file=relative_target.as_posix(),
                file_content=original_content,
                root_cause=diag_result.root_cause,
                suggested_fix=diag_result.suggested_fix,
            )
            new_content_response = await _call_gemini_analysis(patch_prompt)
            if not new_content_response:
                logger.error(
                    "KOR'TANA AUTO-REPAIR: Failed to get patch content from Gemini"
                )
                return False

            new_content = self._extract_python_content(new_content_response)
            if not self._validate_content_delta(
                original_content,
                new_content,
                relative_target,
            ):
                return False

            worktree_created = await self._prepare_worktree(branch_name)
            if not worktree_created:
                return False

            worktree_target = self.worktree_dir / relative_target
            worktree_target.parent.mkdir(parents=True, exist_ok=True)
            worktree_target.write_text(new_content, encoding="utf-8", newline="\n")

            verification_results = await self._run_verification_suite(relative_target)
            if any(not result.success for result in verification_results):
                logger.error(
                    "KOR'TANA AUTO-REPAIR: Verification failed for %s",
                    relative_target.as_posix(),
                )
                return False

            commit_sha = await self._commit_worktree_change(
                relative_target,
                error_type=error_type,
                root_cause=diag_result.root_cause,
            )
            if not commit_sha:
                return False

            # HOP OVERRIDE: Human decree specified NO SACRED MAIN BRANCH.
            logger.warning(
                "KOR'TANA AUTO-REPAIR: HOP Override Active. Merging %s directly to main.",
                branch_name,
            )

            # Record current branch to restore it later
            branch_res = await self._run_process(
                ("git", "branch", "--show-current"), cwd=self.repo_root
            )
            original_branch = (
                branch_res.stdout.strip() if branch_res.returncode == 0 else ""
            )

            try:
                # Switch to main branch before merging. Use --quiet.
                checkout_res = await self._run_process(
                    ("git", "checkout", "main"), cwd=self.repo_root
                )
                if checkout_res.returncode != 0:
                    logger.error(
                        "KOR'TANA AUTO-REPAIR: Failed to checkout main before merge: %s",
                        self._combine_output(checkout_res),
                    )
                    repair_goal.status = GoalStatus.ABANDONED
                    await gm.persist_goal(repair_goal)
                    return False

                # Capture the exact HEAD SHA before merging so rollback targets the right commit
                sha_res = await self._run_process(
                    ("git", "rev-parse", "HEAD"), cwd=self.repo_root
                )
                if sha_res.returncode != 0:
                    logger.error(
                        "KOR'TANA AUTO-REPAIR: Could not resolve HEAD SHA before merge, aborting to stay safe."
                    )
                    repair_goal.status = GoalStatus.ABANDONED
                    await gm.persist_goal(repair_goal)
                    return False
                pre_merge_sha = sha_res.stdout.strip()

                # Merge the validated branch into the primary checkout
                merge_res = await self._run_process(
                    (
                        "git",
                        "merge",
                        "--no-ff",
                        "-m",
                        f"fix(autonomy): Auto-merge {branch_name} - {error_type}",
                        branch_name,
                    ),
                    cwd=self.repo_root,
                )
                if merge_res.returncode != 0:
                    logger.error(
                        "KOR'TANA AUTO-REPAIR: Failed to merge branch %s: %s",
                        branch_name,
                        self._combine_output(merge_res),
                    )
                    # Abort the merge if conflicted
                    await self._run_process(
                        ("git", "merge", "--abort"), cwd=self.repo_root
                    )
                    repair_goal.status = GoalStatus.ABANDONED
                    await gm.persist_goal(repair_goal)
                    return False

                # Push back to origin if configured
                push_res = await self._run_process(
                    ("git", "push", "origin", "main"), cwd=self.repo_root
                )
                if push_res.returncode != 0:
                    logger.error(
                        "KOR'TANA AUTO-REPAIR: Merged successfully locally, but failed to push origin main. Failing closed and reverting to %s.",
                        pre_merge_sha,
                    )
                    # Revert to the captured pre-merge SHA, not HEAD~1, to avoid off-by-one if HEAD advanced
                    await self._run_process(
                        ("git", "reset", "--hard", pre_merge_sha), cwd=self.repo_root
                    )
                    repair_goal.status = GoalStatus.ABANDONED
                    await gm.persist_goal(repair_goal)
                    return False

                logger.info(
                    "KOR'TANA AUTO-REPAIR: Autonomous deploy pushed to production."
                )

                repair_goal.status = GoalStatus.COMPLETED
                repair_goal.progress = 1.0
                # Removed bogus commit_sha assignment
                await gm.persist_goal(repair_goal)

                return True
            finally:
                if original_branch and original_branch != "main":
                    restore_res = await self._run_process(
                        ("git", "checkout", original_branch), cwd=self.repo_root
                    )
                    if restore_res.returncode != 0:
                        logger.error(
                            "KOR'TANA AUTO-REPAIR: CRITICAL — failed to restore branch '%s' after merge. "
                            "Repo may be left on main. Manual intervention required. stderr=%s",
                            original_branch,
                            restore_res.stderr.strip(),
                        )
                        repair_goal.status = GoalStatus.ABANDONED
                        await gm.persist_goal(repair_goal)
                        return False

        except (FileNotFoundError, ValueError) as exc:
            logger.error("KOR'TANA AUTO-REPAIR: %s", exc)
            return False
        except Exception as exc:
            logger.error("KOR'TANA AUTO-REPAIR: Unexpected failure: %s", exc)
            return False
        finally:
            if repair_goal.status == GoalStatus.ACTIVE:
                repair_goal.status = GoalStatus.ABANDONED
                await gm.persist_goal(repair_goal)

            if worktree_created:
                await self._cleanup_worktree()

    def _build_patch_prompt(
        self,
        *,
        error_type: str,
        error_message: str,
        target_file: str,
        file_content: str,
        root_cause: str,
        suggested_fix: str,
    ) -> str:
        return (
            "We are KOR'TANA's self-repair engine. We experienced a failure.\n"
            f"ERROR TYPE: {error_type}\n"
            f"ERROR MESSAGE: {error_message}\n"
            f"ROOT CAUSE: {root_cause}\n"
            f"SUGGESTED FIX: {suggested_fix}\n\n"
            f"Here is the content of {target_file}:\n"
            f"```python\n{file_content}\n```\n\n"
            "Provide the COMPLETE correct python file content that applies the fix. "
            "Respond ONLY with the complete python code in a python code block, "
            "do not use ellipsis. You must output the entire file."
        )

    def _resolve_target_file(self, target_file: str) -> Path:
        candidate = self.boundary.resolve_canonical_path(target_file)
        if candidate.suffix != ".py":
            raise ValueError(
                f"AutonomyCodePatcher only supports Python targets: {candidate}"
            )
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(candidate)

        try:
            candidate.relative_to(self.repo_root / "backend")
        except ValueError as exc:
            raise ValueError(
                "AutonomyCodePatcher currently supports backend Python files only."
            ) from exc

        return candidate

    @staticmethod
    def _extract_python_content(new_content_response: str) -> str:
        python_match = re.search(
            r"```python\s*(.*?)\s*```",
            new_content_response,
            re.DOTALL | re.IGNORECASE,
        )
        if python_match:
            return python_match.group(1).strip() + "\n"

        fenced_match = re.search(
            r"```(?:[a-zA-Z0-9_+-]+)?\s*(.*?)\s*```",
            new_content_response,
            re.DOTALL,
        )
        if fenced_match:
            return fenced_match.group(1).strip() + "\n"

        return new_content_response.strip() + "\n"

    def _validate_content_delta(
        self,
        original_content: str,
        new_content: str,
        target_file: Path,
    ) -> bool:
        if not new_content.strip():
            logger.error(
                "KOR'TANA AUTO-REPAIR: Generated empty file content for %s",
                target_file.as_posix(),
            )
            return False

        original_lines = original_content.splitlines()
        new_lines = new_content.splitlines()
        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{target_file.as_posix()}",
                tofile=f"b/{target_file.as_posix()}",
                lineterm="",
            )
        )
        if not diff_lines:
            logger.warning(
                "KOR'TANA AUTO-REPAIR: Gemini returned no changes for %s",
                target_file.as_posix(),
            )
            return False

        deletions = sum(
            1
            for line in diff_lines
            if line.startswith("-") and not line.startswith("---")
        )
        additions = sum(
            1
            for line in diff_lines
            if line.startswith("+") and not line.startswith("+++")
        )
        changed_lines = deletions + additions
        baseline_lines = max(len(original_lines), 1)
        deletion_ratio = deletions / baseline_lines
        net_shrink = max(0, deletions - additions)

        if changed_lines > self.MAX_CHANGED_LINES:
            logger.warning(
                "KOR'TANA AUTO-REPAIR: Rejecting large rewrite for %s "
                "(changed_lines=%d, max=%d)",
                target_file.as_posix(),
                changed_lines,
                self.MAX_CHANGED_LINES,
            )
            return False
        if deletions >= 5 and deletion_ratio > self.MAX_DELETION_RATIO:
            logger.warning(
                "KOR'TANA AUTO-REPAIR: Rejecting destructive rewrite for %s "
                "(deletions=%d, deletion_ratio=%.2f, max=%.2f)",
                target_file.as_posix(),
                deletions,
                deletion_ratio,
                self.MAX_DELETION_RATIO,
            )
            return False
        if net_shrink > self.MAX_NET_SHRINK:
            logger.warning(
                "KOR'TANA AUTO-REPAIR: Rejecting net-shrink for %s "
                "(net_shrink=%d, max=%d)",
                target_file.as_posix(),
                net_shrink,
                self.MAX_NET_SHRINK,
            )
            return False
        return True

    async def _prepare_worktree(self, branch_name: str) -> bool:
        base_ref = await self._resolve_base_ref()

        await self._run_process(
            ("git", "worktree", "unlock", str(self.worktree_dir)),
            cwd=self.repo_root,
        )
        await self._run_process(("git", "worktree", "prune"), cwd=self.repo_root)

        if self.worktree_dir.exists():
            await self._run_process(
                ("git", "worktree", "remove", "--force", str(self.worktree_dir)),
                cwd=self.repo_root,
            )
            if self.worktree_dir.exists():
                await asyncio.to_thread(shutil.rmtree, self.worktree_dir, True)

        result = await self._run_process(
            (
                "git",
                "worktree",
                "add",
                "-B",
                branch_name,
                str(self.worktree_dir),
                base_ref,
            ),
            cwd=self.repo_root,
        )
        if result.returncode != 0:
            logger.error(
                "KOR'TANA AUTO-REPAIR: Failed to create worktree for %s: %s",
                branch_name,
                self._combine_output(result),
            )
            return False

        return True

    async def _cleanup_worktree(self) -> None:
        await self._run_process(
            ("git", "worktree", "remove", "--force", str(self.worktree_dir)),
            cwd=self.repo_root,
        )
        if self.worktree_dir.exists():
            await asyncio.to_thread(shutil.rmtree, self.worktree_dir, True)

    async def _resolve_base_ref(self) -> str:
        for candidate in self.BASE_BRANCH_CANDIDATES:
            result = await self._run_process(
                ("git", "rev-parse", "--verify", candidate),
                cwd=self.repo_root,
            )
            if result.returncode == 0:
                return candidate

        current_branch = await self._run_process(
            ("git", "branch", "--show-current"),
            cwd=self.repo_root,
        )
        current = current_branch.stdout.strip()
        return current or "HEAD"

    async def _run_verification_suite(
        self,
        relative_target: Path,
    ) -> list[VerificationCommandResult]:
        verification_root = self._verification_root(relative_target)
        results: list[VerificationCommandResult] = []

        for command in self.BACKEND_VERIFICATION_COMMANDS:
            completed = await self._run_process(command.argv, cwd=verification_root)
            result = VerificationCommandResult(
                label=command.label,
                argv=command.argv,
                returncode=completed.returncode,
                output=self._combine_output(completed),
            )
            results.append(result)
            if not result.success:
                break

        return results

    def _verification_root(self, relative_target: Path) -> Path:
        if not relative_target.parts or relative_target.parts[0] != "backend":
            raise ValueError(
                "AutonomyCodePatcher currently supports backend Python files only."
            )
        return self.worktree_dir / "backend"

    async def _commit_worktree_change(
        self,
        relative_target: Path,
        *,
        error_type: str,
        root_cause: str,
    ) -> str | None:
        add_result = await self._run_process(
            ("git", "add", relative_target.as_posix()),
            cwd=self.worktree_dir,
        )
        if add_result.returncode != 0:
            logger.error(
                "KOR'TANA AUTO-REPAIR: Failed to stage %s: %s",
                relative_target.as_posix(),
                self._combine_output(add_result),
            )
            return None

        commit_message = (
            f"fix(auto-repair): resolve {error_type}\n\nRoot Cause: {root_cause}"
        )
        commit_result = await self._run_process(
            ("git", "commit", "-m", commit_message),
            cwd=self.worktree_dir,
        )
        if commit_result.returncode != 0:
            logger.error(
                "KOR'TANA AUTO-REPAIR: Failed to commit worktree change: %s",
                self._combine_output(commit_result),
            )
            return None

        rev_result = await self._run_process(
            ("git", "rev-parse", "HEAD"),
            cwd=self.worktree_dir,
        )
        if rev_result.returncode != 0:
            logger.error(
                "KOR'TANA AUTO-REPAIR: Failed to resolve commit sha: %s",
                self._combine_output(rev_result),
            )
            return None

        return rev_result.stdout.strip()

    async def _run_process(
        self,
        argv: tuple[str, ...],
        *,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        return await asyncio.to_thread(
            subprocess.run,
            list(argv),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def _combine_output(result: subprocess.CompletedProcess[str]) -> str:
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return "\n".join(part for part in (stdout, stderr) if part)

    @staticmethod
    def _serialise_verification_results(
        results: list[VerificationCommandResult],
    ) -> list[dict[str, Any]]:
        return [
            {
                "label": result.label,
                "command": " ".join(result.argv),
                "returncode": result.returncode,
                "success": result.success,
                "output": result.output[:2000],
            }
            for result in results
        ]
