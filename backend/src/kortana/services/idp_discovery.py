"""V13A — IdP Discovery & Config Sync.

Discovers OIDC provider configurations from .well-known/openid-configuration
endpoints and keeps them synchronised.  In offline / test mode the discovery
payloads are registered manually; in production a periodic sync refreshes
the cached provider metadata.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.idp_discovery")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class IdPSyncState(str, Enum):
    """Synchronisation state of a discovered identity provider."""

    PENDING = "pending"
    SYNCED = "synced"
    STALE = "stale"
    FAILED = "failed"


@dataclass
class IdPDiscoveryConfig:
    """Configuration for an IdP discovery endpoint."""

    discovery_url: str = ""
    refresh_interval_hours: int = 24
    auto_sync: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        # Strip trailing slashes for canonical comparison
        self.discovery_url = self.discovery_url.rstrip("/")


@dataclass
class DiscoveredProvider:
    """Metadata extracted from an .well-known/openid-configuration response."""

    discovery_url: str = ""
    issuer: str = ""
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    jwks_uri: str = ""
    userinfo_endpoint: str = ""
    supported_scopes: list[str] = field(default_factory=list)
    supported_response_types: list[str] = field(default_factory=list)
    supported_grant_types: list[str] = field(default_factory=list)
    raw_config: dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""
    discovered_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.config_hash:
            self.config_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {"discovery_url": self.discovery_url, "issuer": self.issuer},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "discovery_url": self.discovery_url,
            "issuer": self.issuer,
            "authorization_endpoint": self.authorization_endpoint,
            "token_endpoint": self.token_endpoint,
            "jwks_uri": self.jwks_uri,
            "userinfo_endpoint": self.userinfo_endpoint,
            "supported_scopes": self.supported_scopes,
            "supported_grant_types": self.supported_grant_types,
            "config_hash": self.config_hash,
            "discovered_at": self.discovered_at.isoformat(),
        }


@dataclass
class IdPSyncEvent:
    """Records a sync attempt for a discovered provider."""

    event_id: str = field(default_factory=lambda: f"sync_{secrets.token_hex(8)}")
    discovery_url: str = ""
    old_config_hash: str = ""
    new_config_hash: str = ""
    sync_state: IdPSyncState = IdPSyncState.PENDING
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_hash: str = ""

    def __post_init__(self) -> None:
        if not self.event_hash:
            self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "event_id": self.event_id,
                "discovery_url": self.discovery_url,
                "sync_state": self.sync_state.value,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "discovery_url": self.discovery_url,
            "old_config_hash": self.old_config_hash,
            "new_config_hash": self.new_config_hash,
            "sync_state": self.sync_state.value,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "event_hash": self.event_hash,
        }


# ---------------------------------------------------------------------------
# IdP Discovery Manager
# ---------------------------------------------------------------------------


class IdPDiscoveryManager:
    """Discovers and synchronises OIDC identity-provider metadata.

    In production this would fetch from ``/.well-known/openid-configuration``.
    For tests / offline usage, use :meth:`register_discovery_payload` to
    inject the JSON document directly.
    """

    def __init__(self) -> None:
        self._configs: dict[str, IdPDiscoveryConfig] = {}
        self._providers: dict[str, DiscoveredProvider] = {}
        self._sync_states: dict[str, IdPSyncState] = {}
        self._sync_events: list[IdPSyncEvent] = []
        self._sync_schedules: dict[str, datetime] = {}

    # -- discovery -----------------------------------------------------------

    def register_discovery_payload(
        self,
        discovery_url: str,
        payload: dict[str, Any],
    ) -> DiscoveredProvider:
        """Register a discovery payload (offline / test mode).

        ``payload`` mirrors the JSON returned by
        ``/.well-known/openid-configuration``.
        """
        discovery_url = discovery_url.rstrip("/")
        provider = DiscoveredProvider(
            discovery_url=discovery_url,
            issuer=payload.get("issuer", ""),
            authorization_endpoint=payload.get("authorization_endpoint", ""),
            token_endpoint=payload.get("token_endpoint", ""),
            jwks_uri=payload.get("jwks_uri", ""),
            userinfo_endpoint=payload.get("userinfo_endpoint", ""),
            supported_scopes=payload.get("scopes_supported", []),
            supported_response_types=payload.get("response_types_supported", []),
            supported_grant_types=payload.get("grant_types_supported", []),
            raw_config=payload,
        )
        old_hash = (
            self._providers[discovery_url].config_hash
            if discovery_url in self._providers
            else ""
        )
        self._providers[discovery_url] = provider
        self._sync_states[discovery_url] = IdPSyncState.SYNCED

        if discovery_url not in self._configs:
            self._configs[discovery_url] = IdPDiscoveryConfig(
                discovery_url=discovery_url,
            )

        self._sync_events.append(
            IdPSyncEvent(
                discovery_url=discovery_url,
                old_config_hash=old_hash,
                new_config_hash=provider.config_hash,
                sync_state=IdPSyncState.SYNCED,
                details="Registered via payload",
            )
        )

        logger.info(
            "Registered IdP discovery: url=%s issuer=%s",
            discovery_url,
            provider.issuer,
        )
        return provider

    def discover(self, discovery_url: str) -> DiscoveredProvider | None:
        """Retrieve a previously discovered provider, or None."""
        return self._providers.get(discovery_url.rstrip("/"))

    # -- sync ----------------------------------------------------------------

    def sync_provider(
        self, discovery_url: str, payload: dict[str, Any] | None = None
    ) -> tuple[DiscoveredProvider | None, str | None]:
        """Synchronise a provider's metadata.

        If ``payload`` is supplied it is used directly (offline mode);
        otherwise this would fetch from the network (not implemented in
        test builds).
        """
        discovery_url = discovery_url.rstrip("/")

        if payload is not None:
            provider = self.register_discovery_payload(discovery_url, payload)
            return provider, None

        existing = self._providers.get(discovery_url)
        if existing is None:
            self._sync_states[discovery_url] = IdPSyncState.FAILED
            self._sync_events.append(
                IdPSyncEvent(
                    discovery_url=discovery_url,
                    sync_state=IdPSyncState.FAILED,
                    details="No payload provided and network fetch not available",
                )
            )
            return None, "No payload provided and network fetch not available"

        # Already synced, mark as synced again
        self._sync_states[discovery_url] = IdPSyncState.SYNCED
        return existing, None

    def schedule_sync(
        self, discovery_url: str, interval_hours: int = 24
    ) -> IdPDiscoveryConfig:
        """Schedule periodic sync for a discovery URL."""
        discovery_url = discovery_url.rstrip("/")
        config = self._configs.get(discovery_url)
        if config is None:
            config = IdPDiscoveryConfig(
                discovery_url=discovery_url,
                refresh_interval_hours=interval_hours,
            )
            self._configs[discovery_url] = config
        else:
            config.refresh_interval_hours = interval_hours

        self._sync_schedules[discovery_url] = datetime.utcnow() + timedelta(
            hours=interval_hours
        )
        return config

    def check_stale_providers(self) -> list[str]:
        """Return discovery URLs whose sync schedule is overdue."""
        now = datetime.utcnow()
        stale: list[str] = []
        for url, next_sync in self._sync_schedules.items():
            if now >= next_sync:
                self._sync_states[url] = IdPSyncState.STALE
                stale.append(url)
        return stale

    # -- queries -------------------------------------------------------------

    def get_sync_status(self, discovery_url: str) -> IdPSyncState | None:
        """Get the current sync state for a discovery URL."""
        return self._sync_states.get(discovery_url.rstrip("/"))

    def list_discovered(self) -> list[DiscoveredProvider]:
        """List all discovered providers."""
        return list(self._providers.values())

    def get_sync_events(self, discovery_url: str | None = None) -> list[IdPSyncEvent]:
        """Get sync events, optionally filtered by discovery URL."""
        if discovery_url is None:
            return list(self._sync_events)
        canonical = discovery_url.rstrip("/")
        return [e for e in self._sync_events if e.discovery_url == canonical]

    @property
    def provider_count(self) -> int:
        return len(self._providers)

    @property
    def event_count(self) -> int:
        return len(self._sync_events)


    def register_with_oidc_registry(self, discovery_url: str) -> bool:
        """Register a discovered provider with the V12A OIDC registry."""
        provider = self._providers.get(discovery_url.rstrip("/"))
        if provider is None:
            return False

        from src.kortana.services.oidc_provider import (
            OIDCConfiguration,
            get_oidc_registry,
        )

        config = OIDCConfiguration(
            issuer_url=provider.issuer,
            client_id=provider.issuer,  # default; caller overrides as needed
            audience=provider.issuer,
        )
        registry = get_oidc_registry()
        registry.register(config, register_with_auth_registry=False)
        logger.info(
            "Registered discovered IdP with OIDC registry: %s", provider.issuer
        )
        return True


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_manager: IdPDiscoveryManager | None = None


def get_idp_discovery_manager() -> IdPDiscoveryManager:
    """Return the module-level IdP discovery manager."""
    global _manager
    if _manager is None:
        _manager = IdPDiscoveryManager()
    return _manager
