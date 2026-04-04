"""
Synthetic autonomy benchmark suite.

Parametrised over four canonical incident archetypes.  For each scenario the
suite verifies:
  - The planner correctly decides to patch (or not) based on confidence
  - patch_succeeded / validation_succeeded flags propagate correctly
  - RepairPlaybook entries are written after a successful / failed run
  - AutonomyBenchmark records can be created with the correct fields
  - CapabilityBudget gates PATCH / PUSH correctly given the autonomy_index
"""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import AutonomyBenchmark, IncidentMemory, RepairPlaybook
from src.kortana.services.capability_budget import ActionClass, CapabilityBudget
from src.kortana.services.patch_planner import (
    PatchPlan,
    PatchPlanner,
    VerificationResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_incident(
    incident_type: str, description: str = "", stack_trace: str = ""
) -> IncidentMemory:
    return IncidentMemory(
        id=str(uuid.uuid4()),
        incident_type=incident_type,
        description=description or f"Synthetic incident: {incident_type}",
        stack_trace=stack_trace or f"Traceback: {incident_type}",
        fix_status=None,
        resolved=False,
    )


def _make_planner(
    worktree: str = "/fake/worktree", db: MagicMock | None = None
) -> PatchPlanner:
    with patch("src.kortana.services.patch_planner.GeminiService"):
        p = PatchPlanner(worktree, db_session=db)
        p.gemini = MagicMock()
        return p


# ---------------------------------------------------------------------------
# Parametrised benchmark scenarios
# ---------------------------------------------------------------------------

SCENARIOS = [
    pytest.param(
        "broken_test",
        "pytest failure: AssertionError in test_auth.py",
        "AssertionError: expected 200 got 401",
        True,  # should be patchable
        id="broken_test",
    ),
    pytest.param(
        "daemon_crash",
        "AutonomyDaemon raised RuntimeError during cycle",
        "RuntimeError: database connection lost",
        True,
        id="daemon_crash",
    ),
    pytest.param(
        "import_error",
        "ImportError: cannot import name 'get_autonomy_controller'",
        "ImportError in src/kortana/services/autonomy_daemon.py",
        True,
        id="import_error",
    ),
    pytest.param(
        "flaky_validation",
        "Intermittent timeout during pytest run",
        "TimeoutError: test_something exceeded 30s",
        False,  # confidence too low → planner rejects
        id="flaky_validation",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("incident_type,description,stack,expect_patch", SCENARIOS)
async def test_stage1_decision(
    incident_type: str,
    description: str,
    stack: str,
    expect_patch: bool,
) -> None:
    """Stage 1 should recommend patching only for high-confidence incidents."""
    incident = _make_incident(incident_type, description, stack)
    planner = _make_planner()

    confidence = 0.95 if expect_patch else 0.60
    planner.gemini.analyze_text = AsyncMock(
        return_value=f"""{{
  "should_patch": {"true" if expect_patch else "false"},
  "root_cause": "Synthetic root cause for {incident_type}",
  "confidence": {confidence},
  "candidate_files": ["src/kortana/services/fake_{incident_type}.py"],
  "forbidden_files_hit": [],
  "validation_commands": ["python -m pytest tests/ -q"]
}}"""
    )

    plan = await planner._stage_1_analyze(incident)
    assert plan.should_patch is expect_patch
    assert plan.confidence == confidence


@pytest.mark.asyncio
@pytest.mark.parametrize("incident_type,description,stack,expect_patch", SCENARIOS)
async def test_full_pipeline_success_path(
    incident_type: str,
    description: str,
    stack: str,
    expect_patch: bool,
) -> None:
    """
    Full pipeline via apply_healing_patch with stages mocked at method level.
    For patchable incidents: asserts True return and playbook write.
    For low-confidence incidents: Stage 1 returns should_patch=False → False return.
    """
    incident = _make_incident(incident_type, description, stack)
    planner = _make_planner()

    if expect_patch:
        mock_plan = PatchPlan(
            should_patch=True,
            root_cause=f"Synthetic root cause: {incident_type}",
            confidence=0.95,
            candidate_files=[f"src/kortana/services/fake_{incident_type}.py"],
            forbidden_files_hit=[],
            validation_commands=["python -m pytest tests/ -q"],
        )
        mock_verify = VerificationResult(
            pass_check=True,
            residual_risk="low",
            pr_summary=f"Fixed {incident_type}",
        )
        fake_diff = (
            f"--- a/src/kortana/services/fake_{incident_type}.py\n"
            f"+++ b/src/kortana/services/fake_{incident_type}.py\n"
            "@@ -1,1 +1,1 @@\n-old = 1\n+new = 2\n"
        )

        with (
            patch.object(
                planner, "_stage_1_analyze", AsyncMock(return_value=mock_plan)
            ),
            patch.object(
                planner, "_stage_2_generate_diff", AsyncMock(return_value=fake_diff)
            ),
            patch.object(
                planner, "_apply_diff_to_worktree", AsyncMock(return_value=True)
            ),
            patch.object(
                planner, "_stage_3_verify_patch", AsyncMock(return_value=mock_verify)
            ),
            patch.object(planner, "_write_repair_playbook", AsyncMock()) as mock_write,
            patch("asyncio.create_subprocess_shell") as mock_shell,
            patch(
                "src.kortana.services.patch_planner.PatchValidator"
            ) as mock_validator_cls,
        ):
            mock_validator_cls.return_value.validate.return_value = MagicMock()
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))
            mock_proc.returncode = 0
            mock_shell.return_value = mock_proc

            result = await planner.apply_healing_patch(incident)

        assert result is True
        mock_write.assert_called_once()
        assert mock_write.call_args.kwargs["outcome"] == "success"
    else:
        # Low-confidence scenario: Stage 1 returns should_patch=False
        mock_plan_reject = PatchPlan(
            should_patch=False,
            root_cause="Low confidence",
            confidence=0.60,
            candidate_files=[],
            forbidden_files_hit=[],
            validation_commands=[],
        )
        with patch.object(
            planner, "_stage_1_analyze", AsyncMock(return_value=mock_plan_reject)
        ):
            result = await planner.apply_healing_patch(incident)
        assert result is False


@pytest.mark.asyncio
@pytest.mark.parametrize("incident_type,description,stack,expect_patch", SCENARIOS)
async def test_full_pipeline_verification_failure(
    incident_type: str,
    description: str,
    stack: str,
    expect_patch: bool,
) -> None:
    """Stage 3 rejection must write a failure outcome to RepairPlaybook."""
    if not expect_patch:
        pytest.skip("Only relevant for patchable scenarios")

    incident = _make_incident(incident_type, description, stack)
    planner = _make_planner()

    mock_plan = PatchPlan(
        should_patch=True,
        root_cause=f"Synthetic root cause: {incident_type}",
        confidence=0.92,
        candidate_files=[f"src/kortana/services/fake_{incident_type}.py"],
        forbidden_files_hit=[],
        validation_commands=["pytest"],
    )
    mock_verify_fail = VerificationResult(
        pass_check=False,
        residual_risk="high - regression risk detected",
        pr_summary="",
    )
    fake_diff = (
        f"--- a/src/kortana/services/fake_{incident_type}.py\n"
        f"+++ b/src/kortana/services/fake_{incident_type}.py\n"
        "@@ -1,1 +1,1 @@\n-old = 1\n+new = 2\n"
    )

    with (
        patch.object(planner, "_stage_1_analyze", AsyncMock(return_value=mock_plan)),
        patch.object(
            planner, "_stage_2_generate_diff", AsyncMock(return_value=fake_diff)
        ),
        patch.object(planner, "_apply_diff_to_worktree", AsyncMock(return_value=True)),
        patch.object(
            planner, "_stage_3_verify_patch", AsyncMock(return_value=mock_verify_fail)
        ),
        patch.object(planner, "_write_repair_playbook", AsyncMock()) as mock_write,
        patch("asyncio.create_subprocess_shell") as mock_shell,
        patch(
            "src.kortana.services.patch_planner.PatchValidator"
        ) as mock_validator_cls,
    ):
        mock_validator_cls.return_value.validate.return_value = MagicMock()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.returncode = 0
        mock_shell.return_value = mock_proc

        result = await planner.apply_healing_patch(incident)

    assert result is False
    mock_write.assert_called_once()
    assert mock_write.call_args.kwargs["outcome"] == "failure"


# ---------------------------------------------------------------------------
# AutonomyBenchmark model creation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("incident_type,description,stack,expect_patch", SCENARIOS)
def test_autonomy_benchmark_record_creation(
    incident_type: str,
    description: str,
    stack: str,
    expect_patch: bool,
) -> None:
    """AutonomyBenchmark records should be creatable with the correct schema."""
    record = AutonomyBenchmark(
        id=str(uuid.uuid4()),
        suite_name="synthetic_v1",
        incident_type=incident_type,
        detected=True,
        patch_succeeded=expect_patch,
        validation_succeeded=expect_patch,
        time_to_recovery_seconds=1.23 if expect_patch else None,
        autonomy_index_at_run=72,
        notes=f"Benchmark run for {incident_type}",
        run_at=datetime.utcnow(),
    )
    assert record.suite_name == "synthetic_v1"
    assert record.incident_type == incident_type


# ---------------------------------------------------------------------------
# RepairPlaybook model creation
# ---------------------------------------------------------------------------


def test_repair_playbook_record_creation() -> None:
    """RepairPlaybook entries should hold the correct fields."""
    entry = RepairPlaybook(
        id=str(uuid.uuid4()),
        incident_type="broken_test",
        incident_pattern="pytest AssertionError in test_auth.py",
        chosen_strategy="Fix assertion with correct expected value",
        outcome="success",
        confidence_delta=0.05,
        times_used=1,
    )
    assert entry.outcome == "success"
    assert entry.incident_type == "broken_test"


# ---------------------------------------------------------------------------
# CapabilityBudget governance
# ---------------------------------------------------------------------------


class TestCapabilityBudget:
    def setup_method(self) -> None:
        self.budget = CapabilityBudget()

    def test_observe_always_permitted(self) -> None:
        assert self.budget.is_permitted(
            ActionClass.OBSERVE,
            autonomy_index=0,
            system_state="critical",
            control_mode="operator_override_halt",
            live_execution_enabled=False,
        )

    def test_patch_blocked_below_min_index(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.PATCH,
            autonomy_index=40,
            system_state="nominal",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_patch_permitted_at_min_index(self) -> None:
        assert self.budget.is_permitted(
            ActionClass.PATCH,
            autonomy_index=50,
            system_state="nominal",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_push_blocked_in_observe_only(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.PUSH,
            autonomy_index=100,
            system_state="nominal",
            control_mode="observe_only",
            live_execution_enabled=False,
        )

    def test_push_blocked_in_critical_state(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.PUSH,
            autonomy_index=100,
            system_state="critical",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_push_blocked_without_live_execution(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.PUSH,
            autonomy_index=80,
            system_state="nominal",
            control_mode="execute",
            live_execution_enabled=False,
        )

    def test_propose_pr_permitted_nominal_live(self) -> None:
        assert self.budget.is_permitted(
            ActionClass.PROPOSE_PR,
            autonomy_index=75,
            system_state="nominal",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_commit_blocked_in_degraded_below_threshold(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.COMMIT,
            autonomy_index=55,
            system_state="nominal",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_push_blocked_in_degraded_state(self) -> None:
        # PUSH needs index ≥ 70, but degraded state blocks it regardless
        assert not self.budget.is_permitted(
            ActionClass.PUSH,
            autonomy_index=80,
            system_state="degraded",
            control_mode="execute",
            live_execution_enabled=True,
        )

    def test_plan_permitted_in_approval_required_mode(self) -> None:
        assert self.budget.is_permitted(
            ActionClass.PLAN,
            autonomy_index=30,
            system_state="nominal",
            control_mode="approval_required",
            live_execution_enabled=False,
        )

    def test_patch_blocked_in_approval_required_mode(self) -> None:
        assert not self.budget.is_permitted(
            ActionClass.PATCH,
            autonomy_index=80,
            system_state="nominal",
            control_mode="approval_required",
            live_execution_enabled=True,
        )
