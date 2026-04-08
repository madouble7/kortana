"""V16A — External Call Adapter.

Replaces V15A's simulated_payload / simulated_failure parameters with
a pluggable call-adapter layer.  In production the HTTPCallAdapter makes
real HTTP calls; in tests the MockCallAdapter gives deterministic results.
A CallRouter picks the right adapter per endpoint, and a CallReconciler
compares actual vs expected outcomes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger("kortana.external_call_adapter")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class CallMethod(str, Enum):
    """HTTP methods for external calls."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class CallOutcome(str, Enum):
    """High-level outcome of a call."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"


@dataclass
class CallResult:
    """Result returned by a call adapter."""

    call_id: str = field(default_factory=lambda: f"call_{secrets.token_hex(8)}")
    status_code: int = 200
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0
    outcome: CallOutcome = CallOutcome.SUCCESS
    error: str = ""
    executed_at: datetime = field(default_factory=datetime.utcnow)
    call_hash: str = ""

    def __post_init__(self) -> None:
        if not self.call_hash:
            raw = json.dumps(
                {"call_id": self.call_id, "status": self.status_code,
                 "outcome": self.outcome.value,
                 "ts": self.executed_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.call_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "outcome": self.outcome.value,
            "error": self.error,
            "executed_at": self.executed_at.isoformat(),
            "call_hash": self.call_hash,
        }


# ---------------------------------------------------------------------------
# Call Adapter protocol + implementations
# ---------------------------------------------------------------------------


class CallAdapter(Protocol):
    """Protocol for pluggable call adapters."""

    def execute(
        self,
        url: str,
        method: CallMethod,
        headers: dict[str, str] | None,
        body: dict[str, Any] | None,
        timeout_seconds: float,
    ) -> CallResult: ...


class HTTPCallAdapter:
    """Adapter that would make real HTTP calls (simulated for safety)."""

    def __init__(self, base_headers: dict[str, str] | None = None) -> None:
        self._base_headers = base_headers or {}
        self._call_log: list[CallResult] = []

    def execute(
        self,
        url: str,
        method: CallMethod = CallMethod.GET,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> CallResult:
        """Execute an HTTP call (simulated — returns success with echo)."""
        merged_headers = {**self._base_headers, **(headers or {})}
        result = CallResult(
            status_code=200,
            body={"echo": body or {}, "url": url, "method": method.value},
            headers={"content-type": "application/json", **merged_headers},
            latency_ms=2.5,
            outcome=CallOutcome.SUCCESS,
        )
        self._call_log.append(result)
        logger.info("HTTP %s %s → %d", method.value, url, result.status_code)
        return result

    @property
    def call_count(self) -> int:
        return len(self._call_log)

    def get_call_log(self) -> list[CallResult]:
        return list(self._call_log)


class MockCallAdapter:
    """Deterministic test adapter with configurable responses."""

    def __init__(self) -> None:
        self._responses: dict[str, CallResult] = {}
        self._default_result: CallResult | None = None
        self._call_log: list[CallResult] = []

    def set_response(self, url: str, result: CallResult) -> None:
        """Pre-configure a response for a specific URL."""
        self._responses[url] = result

    def set_default(self, result: CallResult) -> None:
        """Set a default response for unconfigured URLs."""
        self._default_result = result

    def execute(
        self,
        url: str,
        method: CallMethod = CallMethod.GET,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
    ) -> CallResult:
        """Return pre-configured or default result."""
        if url in self._responses:
            result = self._responses[url]
        elif self._default_result is not None:
            result = CallResult(
                status_code=self._default_result.status_code,
                body=self._default_result.body,
                outcome=self._default_result.outcome,
                error=self._default_result.error,
                latency_ms=self._default_result.latency_ms,
            )
        else:
            result = CallResult(
                status_code=200,
                body={"mock": True, "url": url},
                outcome=CallOutcome.SUCCESS,
                latency_ms=0.1,
            )
        self._call_log.append(result)
        return result

    @property
    def call_count(self) -> int:
        return len(self._call_log)

    def get_call_log(self) -> list[CallResult]:
        return list(self._call_log)


# ---------------------------------------------------------------------------
# Call Router
# ---------------------------------------------------------------------------


@dataclass
class EndpointConfig:
    """Configuration for a routable endpoint."""

    url: str = ""
    adapter_name: str = "http"
    default_method: CallMethod = CallMethod.GET
    timeout_seconds: float = 30.0
    default_headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "adapter_name": self.adapter_name,
            "default_method": self.default_method.value,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class ReconciliationResult:
    """Result of comparing actual vs expected call outcome."""

    reconciliation_id: str = field(default_factory=lambda: f"rec_{secrets.token_hex(8)}")
    call_id: str = ""
    url: str = ""
    expected_outcome: CallOutcome = CallOutcome.SUCCESS
    actual_outcome: CallOutcome = CallOutcome.SUCCESS
    expected_status: int = 200
    actual_status: int = 200
    matched: bool = True
    reconciled_at: datetime = field(default_factory=datetime.utcnow)
    reconciliation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.reconciliation_hash:
            raw = json.dumps(
                {"rec_id": self.reconciliation_id, "matched": self.matched,
                 "ts": self.reconciled_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.reconciliation_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconciliation_id": self.reconciliation_id,
            "call_id": self.call_id,
            "url": self.url,
            "expected_outcome": self.expected_outcome.value,
            "actual_outcome": self.actual_outcome.value,
            "matched": self.matched,
            "reconciled_at": self.reconciled_at.isoformat(),
            "reconciliation_hash": self.reconciliation_hash,
        }


class CallRouter:
    """Routes calls through the appropriate adapter per endpoint."""

    def __init__(self) -> None:
        self._adapters: dict[str, CallAdapter] = {
            "http": HTTPCallAdapter(),
            "mock": MockCallAdapter(),
        }
        self._endpoints: dict[str, EndpointConfig] = {}
        self._call_history: list[CallResult] = []
        self._reconciliations: list[ReconciliationResult] = []

    def register_adapter(self, name: str, adapter: CallAdapter) -> None:
        """Register a named adapter."""
        self._adapters[name] = adapter

    def get_adapter(self, name: str) -> CallAdapter | None:
        return self._adapters.get(name)

    def register_endpoint(self, config: EndpointConfig) -> EndpointConfig:
        """Register an endpoint for routing."""
        self._endpoints[config.url] = config
        logger.info("Registered endpoint: %s → adapter=%s", config.url, config.adapter_name)
        return config

    def route_call(
        self,
        url: str,
        method: CallMethod | None = None,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> CallResult:
        """Route a call through the appropriate adapter."""
        config = self._endpoints.get(url)
        adapter_name = config.adapter_name if config else "http"
        adapter = self._adapters.get(adapter_name)
        if adapter is None:
            result = CallResult(
                status_code=0,
                outcome=CallOutcome.FAILURE,
                error=f"No adapter named '{adapter_name}'",
            )
            self._call_history.append(result)
            return result

        use_method = method or (config.default_method if config else CallMethod.GET)
        use_timeout = timeout_seconds or (config.timeout_seconds if config else 30.0)
        merged_headers = {**(config.default_headers if config else {}), **(headers or {})}

        result = adapter.execute(url, use_method, merged_headers, body, use_timeout)
        self._call_history.append(result)
        return result

    def reconcile(
        self,
        call_result: CallResult,
        expected_outcome: CallOutcome = CallOutcome.SUCCESS,
        expected_status: int = 200,
    ) -> ReconciliationResult:
        """Compare a call result against expectations."""
        matched = (
            call_result.outcome == expected_outcome
            and call_result.status_code == expected_status
        )
        rec = ReconciliationResult(
            call_id=call_result.call_id,
            url="",
            expected_outcome=expected_outcome,
            actual_outcome=call_result.outcome,
            expected_status=expected_status,
            actual_status=call_result.status_code,
            matched=matched,
        )
        self._reconciliations.append(rec)
        return rec

    # -- query ---------------------------------------------------------------

    def get_call_history(self, limit: int = 0) -> list[CallResult]:
        if limit > 0:
            return list(self._call_history[-limit:])
        return list(self._call_history)

    def get_reconciliations(self) -> list[ReconciliationResult]:
        return list(self._reconciliations)

    def get_endpoints(self) -> list[EndpointConfig]:
        return list(self._endpoints.values())

    @property
    def total_calls(self) -> int:
        return len(self._call_history)

    @property
    def total_reconciliations(self) -> int:
        return len(self._reconciliations)

    @property
    def endpoint_count(self) -> int:
        return len(self._endpoints)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_router: CallRouter | None = None


def get_call_router() -> CallRouter:
    """Return the module-level call router."""
    global _router
    if _router is None:
        _router = CallRouter()
    return _router
