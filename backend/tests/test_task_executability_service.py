from src.kortana.models import GitHubTask
from src.kortana.services.task_executability_service import (
    assess_task_executability,
)


def test_assess_task_executability_blocks_abstract_buzzword_task() -> None:
    task = GitHubTask(
        title="Quantum Linkage Integration Framework",
        description="Establish recursive synthesis and architectural resonance.",
    )

    assessment = assess_task_executability(task)

    assert assessment.executable is False
    assert assessment.reason == "abstract_task_without_repo_anchors"


def test_assess_task_executability_allows_repo_anchored_task() -> None:
    task = GitHubTask(
        title="Fix flaky tests in autonomy daemon",
        description=(
            "Update backend/src/kortana/services/autonomy_daemon.py and add "
            "pytest coverage in backend/tests/test_autonomy_daemon.py."
        ),
    )

    assessment = assess_task_executability(task)

    assert assessment.executable is True
    assert assessment.reason == "repo_path_anchor"
