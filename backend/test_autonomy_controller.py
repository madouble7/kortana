import pytest

from src.kortana.services.adaptive_learner import Insight
from src.kortana.services.autonomy_controller import AutonomyController
from src.kortana.services.goal_manager import GoalManager


class StubSelfAwareness:
    def __init__(self, payload):
        self.payload = payload

    async def assess(self):
        return self.payload


class StubLearner:
    def __init__(self, insights):
        self._insights = insights

    def generate_insights(self):
        return self._insights


@pytest.mark.asyncio
async def test_controller_enters_protective_mode_when_system_is_critical(monkeypatch):
    payload = {
        "state": "critical",
        "snapshot": {
            "cpu_percent": 96.0,
            "memory_percent": 93.0,
            "pending_tasks": 4,
            "completed_tasks": 2,
            "failed_tasks": 3,
            "success_rate": 40.0,
        },
        "corrections": [
            {
                "action": "enable_dry_run_mode",
                "reason": "Success rate dropped to 40%",
                "params": {},
            }
        ],
        "capabilities": {
            "ai_consensus": True,
            "ai_providers": True,
            "autonomy_daemon": True,
            "github_integration": True,
            "database": True,
        },
    }
    goal_manager = GoalManager()

    async def fake_get_learner():
        return StubLearner([])

    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_self_awareness",
        lambda: StubSelfAwareness(payload),
    )
    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_adaptive_learner",
        fake_get_learner,
    )
    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_goal_manager",
        lambda: goal_manager,
    )

    controller = AutonomyController()
    reflection = await controller.reflect(
        {"max_tasks_per_cycle": 3, "dry_run_mode": False}
    )

    assert reflection["recommended_controls"]["dry_run_mode"] is True
    assert reflection["recommended_controls"]["max_tasks_per_cycle"] == 1
    assert reflection["recommended_controls"]["focus_mode"] == "stabilize"
    assert reflection["current_focus"]["title"] == "Stabilize autonomous runtime"
    assert reflection["constraints"]


@pytest.mark.asyncio
async def test_controller_increases_throughput_when_runtime_is_healthy(monkeypatch):
    payload = {
        "state": "nominal",
        "snapshot": {
            "cpu_percent": 28.0,
            "memory_percent": 42.0,
            "pending_tasks": 5,
            "completed_tasks": 14,
            "failed_tasks": 1,
            "success_rate": 96.0,
        },
        "corrections": [],
        "capabilities": {
            "ai_consensus": True,
            "ai_providers": True,
            "autonomy_daemon": True,
            "github_integration": True,
            "database": True,
        },
    }
    insights = [
        Insight(
            category="timing",
            summary="gemini is fast AND accurate for 'feature'",
            recommendation="Increase concurrency for 'feature' tasks with gemini",
            confidence=0.8,
        )
    ]
    goal_manager = GoalManager()

    async def fake_get_learner():
        return StubLearner(insights)

    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_self_awareness",
        lambda: StubSelfAwareness(payload),
    )
    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_adaptive_learner",
        fake_get_learner,
    )
    monkeypatch.setattr(
        "src.kortana.services.autonomy_controller.get_goal_manager",
        lambda: goal_manager,
    )

    controller = AutonomyController()
    reflection = await controller.reflect(
        {"max_tasks_per_cycle": 2, "dry_run_mode": False}
    )

    assert reflection["recommended_controls"]["dry_run_mode"] is False
    assert reflection["recommended_controls"]["max_tasks_per_cycle"] >= 3
    assert reflection["recommended_controls"]["focus_mode"] == "execute"
    assert reflection["current_focus"]["title"] == "Process autonomous task backlog"
    assert reflection["autonomy_index"] > 70
