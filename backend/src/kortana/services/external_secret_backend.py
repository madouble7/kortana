"""V14B — External Secret Manager Protocol Adapters.

Extends V13B SecretStoreProvider with Vault, AWS SM, GCP SM, and Azure KV
protocol adapters (simulated for offline testing), rotation scheduling,
and secret-manager health monitoring.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.kortana.services.secret_store import (
    LocalSecretStore,
    SecretBackend,
    SecretReference,
    SecretStoreProvider,
    SecretStoreRegistry,
    SecretValue,
)

logger = logging.getLogger("kortana.external_secret_backend")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@dataclass
class SecretManagerHealth:
    """Health-check result for a secret backend."""

    backend: str = ""
    healthy: bool = True
    latency_ms: float = 0.0
    last_check: datetime = field(default_factory=datetime.utcnow)
    version_info: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "healthy": self.healthy,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat(),
            "version_info": self.version_info,
        }


# ---------------------------------------------------------------------------
# External secret-store adapters (simulated for offline)
# ---------------------------------------------------------------------------


class VaultSecretStore(SecretStoreProvider):
    """HashiCorp Vault KV v2 protocol adapter (simulated)."""

    def __init__(self) -> None:
        self._inner = LocalSecretStore()
        self._name = "vault"

    def store_secret(self, secret_id: str, value: str, path: str = "") -> SecretReference:
        ref = self._inner.store_secret(secret_id, value, path)
        return SecretReference(
            secret_id=ref.secret_id,
            backend=SecretBackend.VAULT,
            path=path or f"secret/data/{secret_id}",
            version=ref.version,
            created_at=ref.created_at,
        )

    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        return self._inner.fetch_secret(secret_id)

    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        ref = self._inner.rotate_secret(secret_id, new_value)
        return SecretReference(
            secret_id=ref.secret_id,
            backend=SecretBackend.VAULT,
            path=ref.path,
            version=ref.version,
            rotated_at=ref.rotated_at,
        )

    def delete_secret(self, secret_id: str) -> bool:
        return self._inner.delete_secret(secret_id)

    def list_secrets(self) -> list[SecretReference]:
        return self._inner.list_secrets()


class AWSSecretStore(SecretStoreProvider):
    """AWS Secrets Manager protocol adapter (simulated)."""

    def __init__(self) -> None:
        self._inner = LocalSecretStore()

    def store_secret(self, secret_id: str, value: str, path: str = "") -> SecretReference:
        ref = self._inner.store_secret(secret_id, value, path)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.AWS_SM,
            path=path or f"arn:aws:secretsmanager:::secret/{secret_id}",
            version=ref.version, created_at=ref.created_at,
        )

    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        return self._inner.fetch_secret(secret_id)

    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        ref = self._inner.rotate_secret(secret_id, new_value)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.AWS_SM,
            path=ref.path, version=ref.version, rotated_at=ref.rotated_at,
        )

    def delete_secret(self, secret_id: str) -> bool:
        return self._inner.delete_secret(secret_id)

    def list_secrets(self) -> list[SecretReference]:
        return self._inner.list_secrets()


class GCPSecretStore(SecretStoreProvider):
    """GCP Secret Manager protocol adapter (simulated)."""

    def __init__(self) -> None:
        self._inner = LocalSecretStore()

    def store_secret(self, secret_id: str, value: str, path: str = "") -> SecretReference:
        ref = self._inner.store_secret(secret_id, value, path)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.GCP_SM,
            path=path or f"projects/-/secrets/{secret_id}/versions/latest",
            version=ref.version, created_at=ref.created_at,
        )

    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        return self._inner.fetch_secret(secret_id)

    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        ref = self._inner.rotate_secret(secret_id, new_value)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.GCP_SM,
            path=ref.path, version=ref.version, rotated_at=ref.rotated_at,
        )

    def delete_secret(self, secret_id: str) -> bool:
        return self._inner.delete_secret(secret_id)

    def list_secrets(self) -> list[SecretReference]:
        return self._inner.list_secrets()


class AzureKeyVaultStore(SecretStoreProvider):
    """Azure Key Vault protocol adapter (simulated)."""

    def __init__(self) -> None:
        self._inner = LocalSecretStore()

    def store_secret(self, secret_id: str, value: str, path: str = "") -> SecretReference:
        ref = self._inner.store_secret(secret_id, value, path)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.AZURE_KV,
            path=path or f"https://vault.azure.net/secrets/{secret_id}",
            version=ref.version, created_at=ref.created_at,
        )

    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        return self._inner.fetch_secret(secret_id)

    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        ref = self._inner.rotate_secret(secret_id, new_value)
        return SecretReference(
            secret_id=ref.secret_id, backend=SecretBackend.AZURE_KV,
            path=ref.path, version=ref.version, rotated_at=ref.rotated_at,
        )

    def delete_secret(self, secret_id: str) -> bool:
        return self._inner.delete_secret(secret_id)

    def list_secrets(self) -> list[SecretReference]:
        return self._inner.list_secrets()


# ---------------------------------------------------------------------------
# Rotation scheduling
# ---------------------------------------------------------------------------


@dataclass
class RotationScheduleEntry:
    """A scheduled secret rotation."""

    secret_id: str = ""
    backend: str = "local"
    interval_hours: int = 24
    next_rotation_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    last_rotated_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_due(self) -> bool:
        return datetime.utcnow() >= self.next_rotation_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_id": self.secret_id,
            "backend": self.backend,
            "interval_hours": self.interval_hours,
            "next_rotation_at": self.next_rotation_at.isoformat(),
            "last_rotated_at": self.last_rotated_at.isoformat() if self.last_rotated_at else None,
            "is_due": self.is_due(),
            "created_at": self.created_at.isoformat(),
        }


class RotationScheduler:
    """Schedules and executes secret rotations."""

    def __init__(self) -> None:
        self._schedules: dict[str, RotationScheduleEntry] = {}

    def schedule_rotation(
        self,
        secret_id: str,
        backend: str = "local",
        interval_hours: int = 24,
    ) -> RotationScheduleEntry:
        """Schedule a recurring rotation."""
        entry = RotationScheduleEntry(
            secret_id=secret_id,
            backend=backend,
            interval_hours=interval_hours,
        )
        self._schedules[secret_id] = entry
        logger.info("Scheduled rotation: %s every %dh", secret_id, interval_hours)
        return entry

    def check_due(self) -> list[RotationScheduleEntry]:
        """Return all rotation schedules that are due."""
        return [e for e in self._schedules.values() if e.is_due()]

    def execute_due_rotations(
        self, registry: SecretStoreRegistry
    ) -> list[tuple[str, bool]]:
        """Execute all due rotations with auto-generated values."""
        results: list[tuple[str, bool]] = []
        for entry in self.check_due():
            new_val = f"rotated_{secrets.token_hex(8)}"
            try:
                registry.rotate_secret(entry.secret_id, new_val, entry.backend)
                entry.last_rotated_at = datetime.utcnow()
                entry.next_rotation_at = datetime.utcnow() + timedelta(
                    hours=entry.interval_hours
                )
                results.append((entry.secret_id, True))
                logger.info("Auto-rotated: %s", entry.secret_id)
            except Exception as exc:
                logger.error("Rotation failed for %s: %s", entry.secret_id, exc)
                results.append((entry.secret_id, False))
        return results

    @property
    def schedule_count(self) -> int:
        return len(self._schedules)

    def get_schedules(self) -> list[RotationScheduleEntry]:
        return list(self._schedules.values())


# ---------------------------------------------------------------------------
# Health monitor
# ---------------------------------------------------------------------------


class SecretHealthMonitor:
    """Monitors health of registered secret backends."""

    def __init__(self, registry: SecretStoreRegistry | None = None) -> None:
        self._registry = registry

    def check_health(self, backend_name: str) -> SecretManagerHealth:
        """Health-check a specific backend."""
        if self._registry is None:
            return SecretManagerHealth(backend=backend_name, healthy=False, version_info="no registry")
        backend = self._registry.get_backend(backend_name)
        if backend is None:
            return SecretManagerHealth(backend=backend_name, healthy=False, version_info="not found")
        # Simulated health check — real implementations would ping the backend
        return SecretManagerHealth(
            backend=backend_name,
            healthy=True,
            latency_ms=1.0,
            version_info=type(backend).__name__,
        )

    def check_all(self) -> list[SecretManagerHealth]:
        """Health-check all registered backends."""
        if self._registry is None:
            return []
        return [self.check_health(name) for name in self._registry.list_backends()]


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_ext_registry: SecretStoreRegistry | None = None


def get_external_secret_registry() -> SecretStoreRegistry:
    """Return a SecretStoreRegistry pre-loaded with external backends."""
    global _ext_registry
    if _ext_registry is None:
        _ext_registry = SecretStoreRegistry()
        _ext_registry.register_backend("vault", VaultSecretStore())
        _ext_registry.register_backend("aws_sm", AWSSecretStore())
        _ext_registry.register_backend("gcp_sm", GCPSecretStore())
        _ext_registry.register_backend("azure_kv", AzureKeyVaultStore())
    return _ext_registry
