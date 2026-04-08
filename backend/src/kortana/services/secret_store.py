"""V13B — Secret-Manager-Backed Key Material.

Provides an abstract secret-store interface with a concrete ``LocalSecretStore``
for development and testing.  Production deployments wire in Vault, AWS SM,
GCP SM, or Azure KV adapters through the same ``SecretStoreRegistry``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.secret_store")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class SecretBackend(str, Enum):
    """Supported secret-management backends."""

    LOCAL = "local"
    VAULT = "vault"
    AWS_SM = "aws_sm"
    GCP_SM = "gcp_sm"
    AZURE_KV = "azure_kv"


@dataclass
class SecretReference:
    """Pointer to a secret stored in a backend."""

    secret_id: str = ""
    backend: SecretBackend = SecretBackend.LOCAL
    path: str = ""
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    rotated_at: datetime | None = None
    ref_hash: str = ""

    def __post_init__(self) -> None:
        if not self.ref_hash:
            self.ref_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "secret_id": self.secret_id,
                "backend": self.backend.value,
                "version": self.version,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_id": self.secret_id,
            "backend": self.backend.value,
            "path": self.path,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "ref_hash": self.ref_hash,
        }


@dataclass
class SecretValue:
    """A fetched secret value. The ``value`` field is redacted in serialisation."""

    ref: SecretReference = field(default_factory=SecretReference)
    value: str = ""
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_id": self.ref.secret_id,
            "backend": self.ref.backend.value,
            "version": self.ref.version,
            "fetched_at": self.fetched_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "value": "***REDACTED***",
        }


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class SecretStoreProvider(ABC):
    """Interface for a secret-management backend."""

    @abstractmethod
    def store_secret(
        self, secret_id: str, value: str, path: str = ""
    ) -> SecretReference:
        ...

    @abstractmethod
    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        ...

    @abstractmethod
    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        ...

    @abstractmethod
    def delete_secret(self, secret_id: str) -> bool:
        ...

    @abstractmethod
    def list_secrets(self) -> list[SecretReference]:
        ...


# ---------------------------------------------------------------------------
# Local (in-memory) implementation
# ---------------------------------------------------------------------------


class LocalSecretStore(SecretStoreProvider):
    """In-memory secret store for development and testing."""

    def __init__(self) -> None:
        self._secrets: dict[str, tuple[SecretReference, str]] = {}

    def store_secret(
        self, secret_id: str, value: str, path: str = ""
    ) -> SecretReference:
        ref = SecretReference(
            secret_id=secret_id,
            backend=SecretBackend.LOCAL,
            path=path or f"/local/{secret_id}",
            version=1,
        )
        self._secrets[secret_id] = (ref, value)
        logger.info("Stored local secret: %s", secret_id)
        return ref

    def fetch_secret(self, secret_id: str) -> SecretValue | None:
        entry = self._secrets.get(secret_id)
        if entry is None:
            return None
        ref, value = entry
        return SecretValue(ref=ref, value=value)

    def rotate_secret(self, secret_id: str, new_value: str) -> SecretReference:
        entry = self._secrets.get(secret_id)
        if entry is None:
            return self.store_secret(secret_id, new_value)

        old_ref, _ = entry
        new_ref = SecretReference(
            secret_id=secret_id,
            backend=SecretBackend.LOCAL,
            path=old_ref.path,
            version=old_ref.version + 1,
            created_at=old_ref.created_at,
            rotated_at=datetime.utcnow(),
        )
        self._secrets[secret_id] = (new_ref, new_value)
        logger.info("Rotated local secret: %s → v%d", secret_id, new_ref.version)
        return new_ref

    def delete_secret(self, secret_id: str) -> bool:
        if secret_id in self._secrets:
            del self._secrets[secret_id]
            logger.info("Deleted local secret: %s", secret_id)
            return True
        return False

    def list_secrets(self) -> list[SecretReference]:
        return [ref for ref, _ in self._secrets.values()]

    @property
    def secret_count(self) -> int:
        return len(self._secrets)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class SecretStoreRegistry:
    """Routes secret operations to the appropriate backend.

    A ``local`` backend is registered by default.
    """

    def __init__(self) -> None:
        self._backends: dict[str, SecretStoreProvider] = {}
        self._default_backend = SecretBackend.LOCAL.value
        # Auto-register local backend
        self._backends[SecretBackend.LOCAL.value] = LocalSecretStore()

    def register_backend(
        self, name: str, provider: SecretStoreProvider
    ) -> None:
        """Register a secret-store backend."""
        self._backends[name] = provider
        logger.info("Registered secret backend: %s", name)

    def get_backend(self, name: str | None = None) -> SecretStoreProvider | None:
        """Get a backend by name (defaults to local)."""
        return self._backends.get(name or self._default_backend)

    def store_secret(
        self,
        secret_id: str,
        value: str,
        backend: str | None = None,
        path: str = "",
    ) -> SecretReference:
        """Store a secret in the named backend."""
        provider = self.get_backend(backend)
        if provider is None:
            raise ValueError(f"Backend {backend!r} not registered")
        return provider.store_secret(secret_id, value, path)

    def fetch_secret(
        self, secret_id: str, backend: str | None = None
    ) -> SecretValue | None:
        """Fetch a secret from the named backend."""
        provider = self.get_backend(backend)
        if provider is None:
            return None
        return provider.fetch_secret(secret_id)

    def rotate_secret(
        self, secret_id: str, new_value: str, backend: str | None = None
    ) -> SecretReference:
        """Rotate a secret in the named backend."""
        provider = self.get_backend(backend)
        if provider is None:
            raise ValueError(f"Backend {backend!r} not registered")
        return provider.rotate_secret(secret_id, new_value)

    def delete_secret(
        self, secret_id: str, backend: str | None = None
    ) -> bool:
        """Delete a secret from the named backend."""
        provider = self.get_backend(backend)
        if provider is None:
            return False
        return provider.delete_secret(secret_id)

    def list_secrets(self, backend: str | None = None) -> list[SecretReference]:
        """List secrets in the named backend."""
        provider = self.get_backend(backend)
        if provider is None:
            return []
        return provider.list_secrets()

    def list_backends(self) -> list[str]:
        """List registered backend names."""
        return list(self._backends.keys())

    @property
    def backend_count(self) -> int:
        return len(self._backends)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_registry: SecretStoreRegistry | None = None


def get_secret_store_registry() -> SecretStoreRegistry:
    """Return the module-level secret-store registry."""
    global _registry
    if _registry is None:
        _registry = SecretStoreRegistry()
    return _registry
