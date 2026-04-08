"""V14A — Automated IdP Metadata Sync.

Extends V13A IdP discovery with scheduled refresh, drift detection, and
automatic reconciliation of IdP metadata changes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.idp_metadata_sync")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class DriftSeverity(str, Enum):
    """Severity of metadata drift."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReconcileAction(str, Enum):
    """Action taken during reconciliation."""

    ACCEPTED = "accepted"
    REVERTED = "reverted"
    ALERTED = "alerted"
    SKIPPED = "skipped"


@dataclass
class MetadataSyncPolicy:
    """Policy governing IdP metadata sync behaviour."""

    sync_interval_minutes: int = 60
    max_drift_tolerance: int = 3
    alert_on_drift: bool = True
    auto_remediate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sync_interval_minutes": self.sync_interval_minutes,
            "max_drift_tolerance": self.max_drift_tolerance,
            "alert_on_drift": self.alert_on_drift,
            "auto_remediate": self.auto_remediate,
        }


@dataclass
class MetadataDrift:
    """A single field-level drift between two metadata snapshots."""

    drift_id: str = field(default_factory=lambda: f"drift_{secrets.token_hex(8)}")
    provider_url: str = ""
    field_name: str = ""
    old_value: str = ""
    new_value: str = ""
    severity: DriftSeverity = DriftSeverity.LOW
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "drift_id": self.drift_id,
            "provider_url": self.provider_url,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity.value,
            "detected_at": self.detected_at.isoformat(),
        }


@dataclass
class MetadataReconciliation:
    """Result of reconciling a drifted provider."""

    reconciliation_id: str = field(
        default_factory=lambda: f"recon_{secrets.token_hex(8)}"
    )
    provider_url: str = ""
    drifts: list[MetadataDrift] = field(default_factory=list)
    action_taken: ReconcileAction = ReconcileAction.SKIPPED
    reconciled_at: datetime = field(default_factory=datetime.utcnow)
    reconciliation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.reconciliation_hash:
            self.reconciliation_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "reconciliation_id": self.reconciliation_id,
                "provider_url": self.provider_url,
                "action_taken": self.action_taken.value,
                "timestamp": self.reconciled_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconciliation_id": self.reconciliation_id,
            "provider_url": self.provider_url,
            "drifts": [d.to_dict() for d in self.drifts],
            "action_taken": self.action_taken.value,
            "reconciled_at": self.reconciled_at.isoformat(),
            "reconciliation_hash": self.reconciliation_hash,
        }


# ---------------------------------------------------------------------------
# IdP Metadata Sync Scheduler
# ---------------------------------------------------------------------------


class IdPMetadataSyncScheduler:
    """Schedules periodic IdP metadata refresh and handles drift."""

    def __init__(self) -> None:
        self._providers: dict[str, MetadataSyncPolicy] = {}
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._drift_history: list[MetadataDrift] = []
        self._reconciliations: list[MetadataReconciliation] = []
        self._sync_history: dict[str, list[dict[str, Any]]] = {}

    def register_provider(
        self, provider_url: str, policy: MetadataSyncPolicy | None = None
    ) -> MetadataSyncPolicy:
        """Register a provider for automated metadata sync."""
        p = policy or MetadataSyncPolicy()
        self._providers[provider_url] = p
        self._snapshots[provider_url] = {}
        self._sync_history.setdefault(provider_url, [])
        logger.info("Registered IdP for metadata sync: %s", provider_url)
        return p

    def update_snapshot(
        self, provider_url: str, metadata: dict[str, Any]
    ) -> None:
        """Update the stored metadata snapshot for a provider."""
        self._snapshots[provider_url] = dict(metadata)
        self._sync_history.setdefault(provider_url, []).append(
            {"timestamp": datetime.utcnow().isoformat(), "fields": list(metadata.keys())}
        )

    def check_drift(
        self, provider_url: str, current_metadata: dict[str, Any] | None = None
    ) -> list[MetadataDrift]:
        """Compare current metadata against stored snapshot and detect drift."""
        stored = self._snapshots.get(provider_url, {})
        if current_metadata is None:
            current_metadata = stored
        if not stored:
            return []

        severity_map: dict[str, DriftSeverity] = {
            "issuer": DriftSeverity.CRITICAL,
            "jwks_uri": DriftSeverity.HIGH,
            "token_endpoint": DriftSeverity.HIGH,
            "authorization_endpoint": DriftSeverity.MEDIUM,
        }
        drifts: list[MetadataDrift] = []
        all_keys = set(stored.keys()) | set(current_metadata.keys())
        for key in all_keys:
            old_val = str(stored.get(key, ""))
            new_val = str(current_metadata.get(key, ""))
            if old_val != new_val:
                drifts.append(
                    MetadataDrift(
                        provider_url=provider_url,
                        field_name=key,
                        old_value=old_val,
                        new_value=new_val,
                        severity=severity_map.get(key, DriftSeverity.LOW),
                    )
                )
        self._drift_history.extend(drifts)
        return drifts

    def reconcile(
        self, provider_url: str, new_metadata: dict[str, Any] | None = None
    ) -> MetadataReconciliation:
        """Reconcile drifted provider metadata."""
        policy = self._providers.get(provider_url)
        drifts = self.check_drift(provider_url, new_metadata) if new_metadata else []

        if not drifts:
            rec = MetadataReconciliation(
                provider_url=provider_url,
                drifts=[],
                action_taken=ReconcileAction.SKIPPED,
            )
            self._reconciliations.append(rec)
            return rec

        # Determine action based on policy
        if policy and policy.auto_remediate:
            action = ReconcileAction.ACCEPTED
            if new_metadata:
                self._snapshots[provider_url] = dict(new_metadata)
        elif policy and policy.alert_on_drift:
            action = ReconcileAction.ALERTED
        else:
            action = ReconcileAction.SKIPPED

        rec = MetadataReconciliation(
            provider_url=provider_url,
            drifts=drifts,
            action_taken=action,
        )
        self._reconciliations.append(rec)
        logger.info(
            "Reconciled %s: action=%s drifts=%d",
            provider_url,
            action.value,
            len(drifts),
        )
        return rec

    def get_sync_history(self, provider_url: str) -> list[dict[str, Any]]:
        """Get sync history for a provider."""
        return list(self._sync_history.get(provider_url, []))

    def get_drift_report(self) -> dict[str, Any]:
        """Get aggregated drift report across all providers."""
        by_provider: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for d in self._drift_history:
            by_provider[d.provider_url] = by_provider.get(d.provider_url, 0) + 1
            by_severity[d.severity.value] = by_severity.get(d.severity.value, 0) + 1
        return {
            "total_drifts": len(self._drift_history),
            "by_provider": by_provider,
            "by_severity": by_severity,
            "reconciliations": len(self._reconciliations),
        }

    @property
    def provider_count(self) -> int:
        return len(self._providers)

    @property
    def drift_count(self) -> int:
        return len(self._drift_history)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_scheduler: IdPMetadataSyncScheduler | None = None


def get_idp_metadata_sync_scheduler() -> IdPMetadataSyncScheduler:
    """Return the module-level IdP metadata sync scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = IdPMetadataSyncScheduler()
    return _scheduler
