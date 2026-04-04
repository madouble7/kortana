"""Tests for runtime model usage telemetry."""

from src.kortana.model_usage_telemetry import get_model_usage_telemetry


def test_model_usage_telemetry_summary_groups_events() -> None:
    telemetry = get_model_usage_telemetry()
    telemetry.reset()

    telemetry.record_generation(
        subsystem="llm_router",
        provider="gemini",
        model="gemini-2.0-flash",
        catalog="llm_router_defaults",
        selection="primary_default",
        runtime_lane="core",
        tokens_used=11,
    )
    telemetry.record_generation(
        subsystem="api_integration",
        provider="groq",
        model="mixtral-8x7b-32768",
        catalog="cost_router_defaults",
        selection="task:summary",
        runtime_lane="core",
    )

    summary = telemetry.get_summary()

    assert summary["total_generations"] == 2
    assert summary["by_subsystem"]["llm_router"] == 1
    assert summary["by_subsystem"]["api_integration"] == 1
    assert summary["by_catalog"]["llm_router_defaults"] == 1
    assert summary["by_provider"]["gemini"] == 1
    assert len(summary["recent"]) == 2
