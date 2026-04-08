"""V17A — Provider Client Registry.

Replaces adapter-safe stubs from V16 with a real provider-client protocol.
Each provider (Kubernetes, Cloud Run, ECS, Terraform, custom) exposes a
uniform lifecycle: connect → deploy → rollback → health-check.  The registry
manages client instances, tracks connection state, and produces auditable
operation records.
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

logger = logging.getLogger("kortana.provider_client_registry")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ProviderType(str, Enum):
    """Supported deployment-provider types."""

    KUBERNETES = "kubernetes"
    CLOUD_RUN = "cloud_run"
    AWS_ECS = "aws_ecs"
    TERRAFORM = "terraform"
    CUSTOM = "custom"


class ClientConnectionState(str, Enum):
    """Connection lifecycle state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    FAILED = "failed"


class ProviderOperationType(str, Enum):
    """Type of operation executed against a provider."""

    CONNECT = "connect"
    DEPLOY = "deploy"
    ROLLBACK = "rollback"
    HEALTH_CHECK = "health_check"
    GET_VERSION = "get_version"
    DISCONNECT = "disconnect"
    SCALE = "scale"


class OperationOutcome(str, Enum):
    """Outcome of a provider operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------


@dataclass
class ProviderClientConfig:
    """Configuration for a provider client."""

    provider_type: ProviderType = ProviderType.KUBERNETES
    name: str = ""
    endpoint: str = ""
    credentials_ref: str = ""
    namespace: str = "default"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    extra_config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_type": self.provider_type.value,
            "name": self.name,
            "endpoint": self.endpoint,
            "namespace": self.namespace,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


@dataclass
class ProviderOperationRecord:
    """Auditable record of a provider operation."""

    operation_id: str = field(default_factory=lambda: f"pop_{secrets.token_hex(8)}")
    provider_name: str = ""
    operation_type: ProviderOperationType = ProviderOperationType.DEPLOY
    version_id: str = ""
    outcome: OperationOutcome = OperationOutcome.SUCCESS
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: str = ""
    executed_at: datetime = field(default_factory=datetime.utcnow)
    operation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.operation_hash:
            raw = json.dumps(
                {"op": self.operation_id, "provider": self.provider_name,
                 "type": self.operation_type.value,
                 "outcome": self.outcome.value,
                 "ts": self.executed_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.operation_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "provider_name": self.provider_name,
            "operation_type": self.operation_type.value,
            "version_id": self.version_id,
            "outcome": self.outcome.value,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "executed_at": self.executed_at.isoformat(),
            "operation_hash": self.operation_hash,
        }


@dataclass
class ProviderHealthReport:
    """Health report from a provider."""

    provider_name: str = ""
    healthy: bool = True
    current_version: str = ""
    replica_count: int = 0
    ready_replicas: int = 0
    connection_state: ClientConnectionState = ClientConnectionState.CONNECTED
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "healthy": self.healthy,
            "current_version": self.current_version,
            "replica_count": self.replica_count,
            "ready_replicas": self.ready_replicas,
            "connection_state": self.connection_state.value,
            "checked_at": self.checked_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Provider Client Protocol
# ---------------------------------------------------------------------------


class ProviderClient(Protocol):
    """Protocol for deployment provider clients."""

    def connect(self) -> bool: ...
    def disconnect(self) -> bool: ...
    def deploy(self, version_id: str) -> ProviderOperationRecord: ...
    def rollback(self, version_id: str) -> ProviderOperationRecord: ...
    def health_check(self) -> ProviderHealthReport: ...
    def get_current_version(self) -> str: ...


# ---------------------------------------------------------------------------
# Simulated Provider Client (test-safe implementation)
# ---------------------------------------------------------------------------


class SimulatedProviderClient:
    """A simulated provider client for testing."""

    def __init__(self, config: ProviderClientConfig) -> None:
        self.config = config
        self._state = ClientConnectionState.DISCONNECTED
        self._current_version = ""
        self._deploy_count = 0
        self._fail_next = False

    def set_fail_next(self, fail: bool = True) -> None:
        """Make the next operation fail (for testing)."""
        self._fail_next = fail

    def connect(self) -> bool:
        if self._fail_next:
            self._fail_next = False
            self._state = ClientConnectionState.FAILED
            return False
        self._state = ClientConnectionState.CONNECTED
        return True

    def disconnect(self) -> bool:
        self._state = ClientConnectionState.DISCONNECTED
        return True

    def deploy(self, version_id: str) -> ProviderOperationRecord:
        if self._fail_next:
            self._fail_next = False
            return ProviderOperationRecord(
                provider_name=self.config.name,
                operation_type=ProviderOperationType.DEPLOY,
                version_id=version_id,
                outcome=OperationOutcome.FAILURE,
                error="Simulated deployment failure",
            )
        self._current_version = version_id
        self._deploy_count += 1
        return ProviderOperationRecord(
            provider_name=self.config.name,
            operation_type=ProviderOperationType.DEPLOY,
            version_id=version_id,
            outcome=OperationOutcome.SUCCESS,
            details={"deploy_count": self._deploy_count},
            latency_ms=15.0,
        )

    def rollback(self, version_id: str) -> ProviderOperationRecord:
        if self._fail_next:
            self._fail_next = False
            return ProviderOperationRecord(
                provider_name=self.config.name,
                operation_type=ProviderOperationType.ROLLBACK,
                version_id=version_id,
                outcome=OperationOutcome.FAILURE,
                error="Simulated rollback failure",
            )
        prev = self._current_version
        self._current_version = version_id
        return ProviderOperationRecord(
            provider_name=self.config.name,
            operation_type=ProviderOperationType.ROLLBACK,
            version_id=version_id,
            outcome=OperationOutcome.SUCCESS,
            details={"previous_version": prev},
            latency_ms=10.0,
        )

    def health_check(self) -> ProviderHealthReport:
        healthy = self._state == ClientConnectionState.CONNECTED
        return ProviderHealthReport(
            provider_name=self.config.name,
            healthy=healthy,
            current_version=self._current_version,
            replica_count=3,
            ready_replicas=3 if healthy else 0,
            connection_state=self._state,
        )

    def get_current_version(self) -> str:
        return self._current_version

    @property
    def state(self) -> ClientConnectionState:
        return self._state


# ---------------------------------------------------------------------------
# Provider Client Registry
# ---------------------------------------------------------------------------


class ProviderClientRegistry:
    """Manages provider client instances and operations."""

    def __init__(self) -> None:
        self._clients: dict[str, SimulatedProviderClient] = {}
        self._configs: dict[str, ProviderClientConfig] = {}
        self._operations: list[ProviderOperationRecord] = []

    def register(self, config: ProviderClientConfig) -> SimulatedProviderClient:
        """Register and create a provider client."""
        client = SimulatedProviderClient(config)
        self._clients[config.name] = client
        self._configs[config.name] = config
        logger.info("Registered provider client: %s (%s)",
                     config.name, config.provider_type.value)
        return client

    def connect(self, name: str) -> ProviderOperationRecord:
        """Connect a provider client."""
        client = self._clients.get(name)
        if client is None:
            return ProviderOperationRecord(
                provider_name=name,
                operation_type=ProviderOperationType.CONNECT,
                outcome=OperationOutcome.FAILURE,
                error="Provider not registered",
            )
        success = client.connect()
        record = ProviderOperationRecord(
            provider_name=name,
            operation_type=ProviderOperationType.CONNECT,
            outcome=OperationOutcome.SUCCESS if success else OperationOutcome.FAILURE,
            error="" if success else "Connection failed",
            latency_ms=5.0,
        )
        self._operations.append(record)
        return record

    def disconnect(self, name: str) -> ProviderOperationRecord:
        """Disconnect a provider client."""
        client = self._clients.get(name)
        if client is None:
            return ProviderOperationRecord(
                provider_name=name,
                operation_type=ProviderOperationType.DISCONNECT,
                outcome=OperationOutcome.FAILURE,
                error="Provider not registered",
            )
        client.disconnect()
        record = ProviderOperationRecord(
            provider_name=name,
            operation_type=ProviderOperationType.DISCONNECT,
            outcome=OperationOutcome.SUCCESS,
        )
        self._operations.append(record)
        return record

    def deploy_version(
        self, name: str, version_id: str,
    ) -> ProviderOperationRecord:
        """Deploy a version through the provider."""
        client = self._clients.get(name)
        if client is None:
            return ProviderOperationRecord(
                provider_name=name,
                operation_type=ProviderOperationType.DEPLOY,
                version_id=version_id,
                outcome=OperationOutcome.FAILURE,
                error="Provider not registered",
            )
        record = client.deploy(version_id)
        self._operations.append(record)
        return record

    def rollback_version(
        self, name: str, version_id: str,
    ) -> ProviderOperationRecord:
        """Rollback to a version through the provider."""
        client = self._clients.get(name)
        if client is None:
            return ProviderOperationRecord(
                provider_name=name,
                operation_type=ProviderOperationType.ROLLBACK,
                version_id=version_id,
                outcome=OperationOutcome.FAILURE,
                error="Provider not registered",
            )
        record = client.rollback(version_id)
        self._operations.append(record)
        return record

    def health_check(self, name: str) -> ProviderHealthReport:
        """Run a health check for a provider."""
        client = self._clients.get(name)
        if client is None:
            return ProviderHealthReport(
                provider_name=name,
                healthy=False,
                connection_state=ClientConnectionState.DISCONNECTED,
            )
        return client.health_check()

    def get_client(self, name: str) -> SimulatedProviderClient | None:
        return self._clients.get(name)

    def get_status(self, name: str) -> dict[str, Any]:
        """Get current status of a provider."""
        client = self._clients.get(name)
        config = self._configs.get(name)
        if client is None or config is None:
            return {"error": "Provider not registered"}
        return {
            "name": name,
            "provider_type": config.provider_type.value,
            "connection_state": client.state.value,
            "current_version": client.get_current_version(),
        }

    def list_providers(self) -> list[dict[str, Any]]:
        return [self.get_status(n) for n in self._clients]

    def get_operations(
        self, name: str = "", op_type: ProviderOperationType | None = None,
    ) -> list[ProviderOperationRecord]:
        ops = list(self._operations)
        if name:
            ops = [o for o in ops if o.provider_name == name]
        if op_type:
            ops = [o for o in ops if o.operation_type == op_type]
        return ops

    @property
    def provider_count(self) -> int:
        return len(self._clients)

    @property
    def total_operations(self) -> int:
        return len(self._operations)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_registry: ProviderClientRegistry | None = None


def get_provider_client_registry() -> ProviderClientRegistry:
    """Return the module-level provider client registry."""
    global _registry
    if _registry is None:
        _registry = ProviderClientRegistry()
    return _registry
