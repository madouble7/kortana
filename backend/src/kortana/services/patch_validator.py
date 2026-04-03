"""
PatchValidator — Middleware guardrail for autonomous patch safety.

Sits between PatchPlanner.Stage 2 output and worktree application.
Enforces hard limits that prevent destructive rewrites from being applied
even if the LLM returned should_patch=true and confidence ≥ 0.80.

Three independent checks run synchronously (no LLM call):
  1. Line-Deletion Ratio (LDR):  deletions / original_file_lines ≤ MAX_LDR
  2. Net-Shrink Guard:           (deletions - additions) must not exceed MAX_NET_SHRINK
  3. Context-Availability (CA):  fraction of snippets that are unavailable sentinels

Each failing check returns a :class:`ValidationFailure` with a reason string.
All checks pass → :class:`ValidationOK`.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tuneable thresholds (change here; tests will catch regressions)
# ---------------------------------------------------------------------------

# Maximum fraction of a file's original lines that a patch may delete.
# 0.40 → at most 40 % of original lines may be removed in one patch.
MAX_LDR: float = 0.40

# Maximum raw net-shrink in lines across the entire diff.
# Safeguard for multi-file patches that each stay under the ratio but together
# constitute a destructive rewrite.
MAX_NET_SHRINK: int = 120

# Maximum fraction of context snippet slots that may carry an
# [Context Unavailable] sentinel.  Above this → "High Risk – Partial Context".
MAX_UNAVAILABLE_CONTEXT_FRACTION: float = 0.50


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class ValidationOK:
    ldr: float
    net_shrink: int
    unavailable_fraction: float


@dataclass
class ValidationFailure:
    reasons: List[str] = field(default_factory=list)
    ldr: float = 0.0
    net_shrink: int = 0
    unavailable_fraction: float = 0.0

    def summary(self) -> str:
        return "; ".join(self.reasons)


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------


class PatchValidator:
    """Stateless middleware that validates a unified diff before worktree apply.

    Usage::

        validator = PatchValidator(worktree_dir)
        result = validator.validate(diff, context_snippets_text)
        if isinstance(result, ValidationFailure):
            logger.warning("Patch rejected: %s", result.summary())
            return False
    """

    def __init__(self, worktree_dir: str):
        self.worktree_dir = worktree_dir

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def validate(
        self,
        diff: str,
        context_snippets: str = "",
        *,
        max_ldr: float = MAX_LDR,
        max_net_shrink: int = MAX_NET_SHRINK,
        max_unavailable: float = MAX_UNAVAILABLE_CONTEXT_FRACTION,
    ) -> ValidationOK | ValidationFailure:
        """Run all checks and return OK or Failure (never raises)."""
        failures: list[str] = []

        ldr, net_shrink = self._analyse_diff(diff)
        unavailable_fraction = self._analyse_context(context_snippets)

        # Check 1: Line-Deletion Ratio
        if ldr > max_ldr:
            failures.append(
                f"LDR {ldr:.0%} exceeds threshold {max_ldr:.0%} — destructive rewrite suspected"
            )
            logger.warning(
                "PatchValidator: LDR=%.2f exceeds max=%.2f — patch blocked", ldr, max_ldr
            )

        # Check 2: Net-Shrink Guard
        if net_shrink > max_net_shrink:
            failures.append(
                f"Net shrink {net_shrink} lines exceeds threshold {max_net_shrink}"
            )
            logger.warning(
                "PatchValidator: net_shrink=%d exceeds max=%d — patch blocked",
                net_shrink,
                max_net_shrink,
            )

        # Check 3: Context Availability
        if unavailable_fraction > max_unavailable:
            failures.append(
                f"Context unavailable for {unavailable_fraction:.0%} of referenced files "
                f"(threshold {max_unavailable:.0%}) — High Risk: Partial Context"
            )
            logger.warning(
                "PatchValidator: unavailable_fraction=%.2f exceeds max=%.2f — patch blocked",
                unavailable_fraction,
                max_unavailable,
            )

        if failures:
            return ValidationFailure(
                reasons=failures,
                ldr=ldr,
                net_shrink=net_shrink,
                unavailable_fraction=unavailable_fraction,
            )

        logger.debug(
            "PatchValidator: OK (ldr=%.2f, net_shrink=%d, unavailable=%.2f)",
            ldr,
            net_shrink,
            unavailable_fraction,
        )
        return ValidationOK(ldr=ldr, net_shrink=net_shrink, unavailable_fraction=unavailable_fraction)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyse_diff(self, diff: str) -> tuple[float, int]:
        """Return (max_file_ldr, total_net_shrink) for the diff.

        max_file_ldr = max over all modified files of (deletions / original_lines).
        total_net_shrink = sum(deletions) - sum(additions) across all files.
        """
        # Parse per-file hunk stats from unified diff
        # Hunk headers: @@ -start[,count] +start[,count] @@
        file_deletions: dict[str, int] = {}
        file_additions: dict[str, int] = {}
        current_file: Optional[str] = None

        for line in diff.splitlines():
            if line.startswith("--- "):
                # "--- a/path/to/file.py" or "--- /dev/null"
                raw = line[4:].strip()
                # strip a/ b/ prefixes from git diff
                for prefix in ("a/", "b/"):
                    if raw.startswith(prefix):
                        raw = raw[2:]
                        break
                current_file = raw
                file_deletions.setdefault(current_file, 0)
                file_additions.setdefault(current_file, 0)
            elif line.startswith("-") and not line.startswith("---"):
                if current_file:
                    file_deletions[current_file] = file_deletions.get(current_file, 0) + 1
            elif line.startswith("+") and not line.startswith("+++"):
                if current_file:
                    file_additions[current_file] = file_additions.get(current_file, 0) + 1

        total_deletions = sum(file_deletions.values())
        total_additions = sum(file_additions.values())
        net_shrink = max(0, total_deletions - total_additions)

        # Compute LDR per file using actual worktree line counts
        max_ldr = 0.0
        for fname, deletions in file_deletions.items():
            if deletions == 0:
                continue
            original_lines = self._count_file_lines(fname)
            if original_lines > 0:
                ratio = deletions / original_lines
            else:
                # File not found in worktree — treat ratio as 1.0 (total deletion)
                ratio = 1.0
            if ratio > max_ldr:
                max_ldr = ratio

        return max_ldr, net_shrink

    def _count_file_lines(self, rel_path: str) -> int:
        """Return the number of lines in the worktree file, or 0 if not found."""
        abs_path = os.path.join(self.worktree_dir, rel_path)
        try:
            with open(abs_path, encoding="utf-8", errors="replace") as fh:
                return sum(1 for _ in fh)
        except OSError:
            return 0

    @staticmethod
    def _analyse_context(context_snippets: str) -> float:
        """Return the fraction of snippet blocks that carry an unavailable sentinel."""
        if not context_snippets:
            return 0.0

        # Each snippet starts with "# path/..."
        blocks = re.split(r"\n# ", context_snippets)
        # Drop empty leading split artifact
        blocks = [b for b in blocks if b.strip()]
        if not blocks:
            return 0.0

        unavailable = sum(1 for b in blocks if "Context Unavailable" in b)
        return unavailable / len(blocks)
