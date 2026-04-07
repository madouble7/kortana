from __future__ import annotations

import re
from dataclasses import dataclass

from src.kortana.models import GitHubTask


_FILE_PATH_RE = re.compile(
    r"\b(?:backend|frontend|src|tests|autonomy_loop|docs)/[A-Za-z0-9_./-]+\b"
)
_FILE_EXT_RE = re.compile(
    r"\b[A-Za-z0-9_./-]+\.(?:py|ts|tsx|js|jsx|json|md|toml|yml|yaml|css|sql)\b"
)

_ACTION_TERMS = {
    "add",
    "fix",
    "refactor",
    "remove",
    "rename",
    "update",
    "implement",
    "write",
    "create",
    "repair",
    "harden",
    "expand",
    "consolidate",
    "expose",
}

_CODE_TARGET_TERMS = {
    "endpoint",
    "router",
    "service",
    "function",
    "class",
    "model",
    "schema",
    "migration",
    "test",
    "pytest",
    "mypy",
    "ruff",
    "branch",
    "queue",
    "daemon",
    "memory",
    "metrics",
    "api",
    "path",
    "file",
}

_ABSTRACT_TERMS = {
    "architecture",
    "consciousness",
    "ecosystem",
    "framework",
    "harmony",
    "integration",
    "linkage",
    "philosophical",
    "platform",
    "quantum",
    "resonance",
    "singularity",
    "strategy",
    "synthesis",
    "transcendent",
    "vision",
}

_ABSTRACT_PHRASES = (
    "integration framework",
    "quantum linkage",
    "reactive processing synthesis",
    "architectural resonance",
    "consciousness expansion",
)


@dataclass(frozen=True)
class ExecutabilityAssessment:
    executable: bool
    reason: str
    concrete_hits: int
    abstract_hits: int


def assess_task_executability(task: GitHubTask) -> ExecutabilityAssessment:
    title = task.title or ""
    description = getattr(task, "description", "") or getattr(task, "body", "") or ""
    corpus = f"{title}\n{description}".lower()

    path_hits = len(_FILE_PATH_RE.findall(corpus)) + len(_FILE_EXT_RE.findall(corpus))
    action_hits = _count_keyword_hits(corpus, _ACTION_TERMS)
    target_hits = _count_keyword_hits(corpus, _CODE_TARGET_TERMS)
    abstract_hits = _count_keyword_hits(corpus, _ABSTRACT_TERMS)
    phrase_hits = sum(1 for phrase in _ABSTRACT_PHRASES if phrase in corpus)

    concrete_hits = path_hits + action_hits + target_hits
    total_abstract = abstract_hits + (phrase_hits * 2)

    if path_hits > 0:
        return ExecutabilityAssessment(
            executable=True,
            reason="repo_path_anchor",
            concrete_hits=concrete_hits,
            abstract_hits=total_abstract,
        )

    if action_hits >= 1 and target_hits >= 1:
        return ExecutabilityAssessment(
            executable=True,
            reason="concrete_action_and_target",
            concrete_hits=concrete_hits,
            abstract_hits=total_abstract,
        )

    if total_abstract >= 3 and concrete_hits <= 1:
        return ExecutabilityAssessment(
            executable=False,
            reason="abstract_task_without_repo_anchors",
            concrete_hits=concrete_hits,
            abstract_hits=total_abstract,
        )

    return ExecutabilityAssessment(
        executable=True,
        reason="allowed_by_default",
        concrete_hits=concrete_hits,
        abstract_hits=total_abstract,
    )


def _count_keyword_hits(corpus: str, keywords: set[str]) -> int:
    return sum(1 for keyword in keywords if re.search(rf"\b{re.escape(keyword)}\b", corpus))
