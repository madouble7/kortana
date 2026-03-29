import pytest
from unittest.mock import AsyncMock, patch

from src.kortana.models import IncidentMemory
from src.kortana.services.patch_planner import PatchPlanner, PatchPlan, VerificationResult

@pytest.fixture
def mock_incident():
    return IncidentMemory(
        id=1,
        incident_type="test_error",
        description="Tests failing in backend.",
        stack_trace="AssertionError: 1 != 2",
        fix_status="OPEN"
    )

@pytest.fixture
def planner():
    with patch('src.kortana.services.patch_planner.GeminiService') as mock_gemini:
        # Give the planner a fake worktree dir
        p = PatchPlanner("/tmp/fake_worktree")
        p.gemini = mock_gemini.return_value
        yield p

@pytest.mark.asyncio
async def test_stage_1_analyze_success(planner, mock_incident):
    planner.gemini.analyze_text = AsyncMock(return_value='''{
        "should_patch": true,
        "root_cause": "Typo in test",
        "confidence": 0.95,
        "candidate_files": ["backend/tests/test_mock.py"],
        "forbidden_files_hit": [],
        "validation_commands": ["pytest"]
    }''')

    plan = await planner._stage_1_analyze(mock_incident)
    assert plan.should_patch is True
    assert plan.confidence == 0.95
    assert len(plan.candidate_files) == 1

@pytest.mark.asyncio
async def test_stage_1_analyze_forbidden_files_hit(planner, mock_incident):
    planner.gemini.analyze_text = AsyncMock(return_value='''{
        "should_patch": true,
        "root_cause": "Needs env change",
        "confidence": 0.9,
        "candidate_files": [".env"],
        "forbidden_files_hit": [".env"],
        "validation_commands": []
    }''')

    plan = await planner._stage_1_analyze(mock_incident)
    assert plan.forbidden_files_hit == [".env"]

@pytest.mark.asyncio
async def test_stage_2_generate_diff_too_many_files(planner, mock_incident):
    plan = PatchPlan(
        should_patch=True,
        root_cause="Fix",
        confidence=0.9,
        candidate_files=["file1.py", "file2.py", "file3.py", "file4.py"],
        forbidden_files_hit=[],
        validation_commands=[]
    )
    diff = await planner._stage_2_generate_diff(mock_incident, plan)
    assert diff is None  # Guardrail hit

@pytest.mark.asyncio
async def test_stage_2_generate_diff_forbidden_prefix(planner, mock_incident):
    plan = PatchPlan(
        should_patch=True,
        root_cause="Fix",
        confidence=0.9,
        candidate_files=["backend/auth/secret.py"],
        forbidden_files_hit=[],
        validation_commands=[]
    )
    diff = await planner._stage_2_generate_diff(mock_incident, plan)
    assert diff is None  # Guardrail hit

@pytest.mark.asyncio
async def test_apply_healing_patch_success(planner, mock_incident):
    planner._stage_1_analyze = AsyncMock(return_value=PatchPlan(
        should_patch=True, root_cause="Fix", confidence=0.9,
        candidate_files=["test.py"], forbidden_files_hit=[], validation_commands=[]
    ))
    planner._stage_2_generate_diff = AsyncMock(return_value="--- a/test.py\n+++ b/test.py\n+fix")
    planner._apply_diff_to_worktree = AsyncMock(return_value=True)
    planner._stage_3_verify_patch = AsyncMock(return_value=VerificationResult(
        pass_check=True, residual_risk="None", pr_summary="Fixed issue"
    ))

    success = await planner.apply_healing_patch(mock_incident)
    assert success is True
    planner._stage_1_analyze.assert_called_once()
    planner._stage_2_generate_diff.assert_called_once()
    planner._apply_diff_to_worktree.assert_called_once()
    planner._stage_3_verify_patch.assert_called_once()

@pytest.mark.asyncio
async def test_apply_healing_patch_rejected_by_analysis(planner, mock_incident):
    planner._stage_1_analyze = AsyncMock(return_value=PatchPlan(
        should_patch=False, root_cause="Too complex", confidence=0.4,
        candidate_files=[], forbidden_files_hit=[], validation_commands=[]
    ))

    success = await planner.apply_healing_patch(mock_incident)
    assert success is False