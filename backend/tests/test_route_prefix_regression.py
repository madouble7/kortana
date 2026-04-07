"""Regression tests for duplicated router prefixes in the main app."""


def test_openapi_uses_single_route_prefixes():
    from src.kortana.main import app

    paths = app.openapi().get("paths", {})

    assert "/api/task-queue/" in paths
    assert "/api/optimization/health" in paths
    assert "/api/orchestration/meta/initialize" in paths
    assert "/api/system/health/" in paths

    assert "/api/task-queue/api/tasks/" not in paths
    assert "/api/optimization/api/optimization/health" not in paths
    assert "/api/orchestration/meta/api/orchestration/meta/initialize" not in paths
    assert "/api/system/health/api/health/" not in paths
