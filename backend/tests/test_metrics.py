"""
Tests for metrics module - verifies PrometheusCounter/Gauge/Histogram objects
and the utility functions for recording metrics.
"""


class TestMetricsModuleImport:
    """Tests that metrics objects are instantiated correctly at module level."""

    def test_http_requests_total_counter(self):
        from src.kortana.metrics import http_requests_total

        # Should be a Counter with the correct labels
        assert http_requests_total is not None

    def test_http_request_duration_histogram(self):
        from src.kortana.metrics import http_request_duration_seconds

        assert http_request_duration_seconds is not None

    def test_http_requests_in_progress_gauge(self):
        from src.kortana.metrics import http_requests_in_progress

        assert http_requests_in_progress is not None

    def test_agent_executions_counter(self):
        from src.kortana.metrics import agent_executions_total

        assert agent_executions_total is not None

    def test_agent_execution_duration_histogram(self):
        from src.kortana.metrics import agent_execution_duration_seconds

        assert agent_execution_duration_seconds is not None

    def test_all_counters_present(self):
        from src.kortana.metrics import (
            api_key_requests_total,
            auth_failures_total,
            cache_hits_total,
            cache_misses_total,
            errors_total,
            github_api_calls_total,
            llm_provider_calls_total,
            llm_tokens_used_total,
            memory_operations_total,
            rate_limit_hits_total,
            task_queue_operations_total,
        )

        for metric in [
            api_key_requests_total,
            auth_failures_total,
            cache_hits_total,
            cache_misses_total,
            errors_total,
            github_api_calls_total,
            llm_provider_calls_total,
            llm_tokens_used_total,
            memory_operations_total,
            rate_limit_hits_total,
            task_queue_operations_total,
        ]:
            assert metric is not None

    def test_all_gauges_present(self):
        from src.kortana.metrics import (
            db_connections_active,
            db_connections_idle,
            redis_connections_active,
        )

        for metric in [
            db_connections_active,
            db_connections_idle,
            redis_connections_active,
        ]:
            assert metric is not None

    def test_app_info_present(self):
        from src.kortana.metrics import app_info

        assert app_info is not None


class TestTrackRequest:
    """Tests for the track_request function."""

    def test_track_request_increments_counter(self):
        from src.kortana.metrics import http_requests_total, track_request

        # Get the current count before
        labels = {"method": "GET", "endpoint": "/test-metrics", "status_code": "200"}
        before = http_requests_total.labels(**labels)._value.get()
        track_request("GET", "/test-metrics", 200, 0.1)
        after = http_requests_total.labels(**labels)._value.get()
        assert after == before + 1

    def test_track_request_records_duration(self):
        from src.kortana.metrics import track_request

        # Just verify it doesn't throw
        track_request("POST", "/test/endpoint", 201, 0.5)

    def test_track_request_various_status_codes(self):
        from src.kortana.metrics import track_request

        for status_code in [200, 201, 400, 401, 404, 500]:
            track_request("GET", f"/test/{status_code}", status_code, 0.01)


class TestTrackAgentExecution:
    """Tests for track_agent_execution function."""

    def test_track_agent_execution_success(self):
        from src.kortana.metrics import track_agent_execution

        track_agent_execution("agent-001", "success", 1.5)

    def test_track_agent_execution_failure(self):
        from src.kortana.metrics import track_agent_execution

        track_agent_execution("agent-001", "failure", 0.1)


class TestTrackLLMCall:
    """Tests for track_llm_call function."""

    def test_track_llm_call_with_tokens(self):
        from src.kortana.metrics import track_llm_call

        track_llm_call("gemini", "gemini-pro", "success", 500)

    def test_track_llm_call_zero_tokens(self):
        from src.kortana.metrics import track_llm_call

        track_llm_call("gemini", "gemini-pro", "success", 0)

    def test_track_llm_call_failure(self):
        from src.kortana.metrics import track_llm_call

        track_llm_call("openai", "gpt-4", "failure")


class TestTrackCacheHit:
    """Tests for track_cache_hit function."""

    def test_track_cache_hit_true(self):
        from src.kortana.metrics import track_cache_hit

        track_cache_hit(True)

    def test_track_cache_hit_false(self):
        from src.kortana.metrics import track_cache_hit

        track_cache_hit(False)


class TestTrackAuthFailure:
    """Tests for track_auth_failure function."""

    def test_track_auth_invalid_creds(self):
        from src.kortana.metrics import track_auth_failure

        track_auth_failure("invalid_credentials")

    def test_track_auth_expired_token(self):
        from src.kortana.metrics import track_auth_failure

        track_auth_failure("expired_token")


class TestTrackError:
    """Tests for track_error function."""

    def test_track_error(self):
        from src.kortana.metrics import track_error

        track_error("ValueError", "/api/test")

    def test_track_error_500(self):
        from src.kortana.metrics import track_error

        track_error("InternalServerError", "/api/crash")


class TestGetMetricsOutput:
    """Tests for generate_latest via registry."""

    def test_generate_latest_returns_bytes(self):
        from prometheus_client import generate_latest

        from src.kortana.metrics import registry

        output = generate_latest(registry)
        assert isinstance(output, bytes)

    def test_generate_latest_contains_kortana_prefix(self):
        from prometheus_client import generate_latest

        from src.kortana.metrics import registry

        output = generate_latest(registry)
        assert b"kortana" in output


class TestSetAppInfo:
    """Tests for set_app_info function."""

    def test_set_app_info(self):
        from src.kortana.metrics import set_app_info

        set_app_info("1.2.3", "production")

    def test_set_app_info_defaults(self):
        from src.kortana.metrics import set_app_info

        set_app_info()

    def test_set_app_info_testing(self):
        from src.kortana.metrics import set_app_info

        set_app_info("0.0.1", "testing")
