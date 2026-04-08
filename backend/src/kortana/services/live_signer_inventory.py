"""V14C — Live Signer Inventory & Certificate Validation.

Extends V13C CIAttestationVerifier with a live signer registry that tracks
certificate lifecycle, supports revocation, and validates attestation
payloads against the current signer inventory.
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

logger = logging.getLogger("kortana.live_signer_inventory")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class SignerStatus(str, Enum):
    """Lifecycle status of a signer certificate."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


@dataclass
class SignerCertificate:
    """Certificate metadata for a registered signer."""

    signer_id: str = ""
    certificate_hash: str = ""
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=365)
    )
    issuer: str = ""
    status: SignerStatus = SignerStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.certificate_hash:
            self.certificate_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "signer_id": self.signer_id,
                "issuer": self.issuer,
                "issued_at": self.issued_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.status == SignerStatus.ACTIVE and not self.is_expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "signer_id": self.signer_id,
            "certificate_hash": self.certificate_hash,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "issuer": self.issuer,
            "status": self.status.value,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
        }


@dataclass
class SignerRevocationEntry:
    """Record of a signer revocation."""

    signer_id: str = ""
    revoked_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    revoked_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "signer_id": self.signer_id,
            "revoked_at": self.revoked_at.isoformat(),
            "reason": self.reason,
            "revoked_by": self.revoked_by,
        }


@dataclass
class SignerInventory:
    """Snapshot of the current signer registry."""

    inventory_id: str = field(
        default_factory=lambda: f"inv_{secrets.token_hex(8)}"
    )
    signers: dict[str, SignerCertificate] = field(default_factory=dict)
    last_synced: datetime = field(default_factory=datetime.utcnow)
    inventory_hash: str = ""

    def __post_init__(self) -> None:
        if not self.inventory_hash:
            self.inventory_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "inventory_id": self.inventory_id,
                "signer_count": len(self.signers),
                "synced": self.last_synced.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "signers": {k: v.to_dict() for k, v in self.signers.items()},
            "signer_count": len(self.signers),
            "last_synced": self.last_synced.isoformat(),
            "inventory_hash": self.inventory_hash,
        }


# ---------------------------------------------------------------------------
# Live signer registry
# ---------------------------------------------------------------------------


class LiveSignerRegistry:
    """Live signer inventory with certificate lifecycle management."""

    def __init__(self) -> None:
        self._signers: dict[str, SignerCertificate] = {}
        self._revocations: list[SignerRevocationEntry] = []

    def register_signer(
        self,
        signer_id: str,
        issuer: str = "",
        expires_in_days: int = 365,
    ) -> SignerCertificate:
        """Register a signer with a certificate."""
        cert = SignerCertificate(
            signer_id=signer_id,
            issuer=issuer,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
        )
        self._signers[signer_id] = cert
        logger.info("Registered signer: %s (issuer=%s)", signer_id, issuer)
        return cert

    def revoke_signer(
        self, signer_id: str, reason: str = "", revoked_by: str = ""
    ) -> SignerRevocationEntry | None:
        """Revoke a signer's certificate."""
        cert = self._signers.get(signer_id)
        if cert is None:
            return None
        cert.status = SignerStatus.REVOKED
        entry = SignerRevocationEntry(
            signer_id=signer_id, reason=reason, revoked_by=revoked_by
        )
        self._revocations.append(entry)
        logger.info("Revoked signer: %s reason=%s", signer_id, reason)
        return entry

    def check_signer_status(self, signer_id: str) -> SignerStatus | None:
        """Check the status of a signer."""
        cert = self._signers.get(signer_id)
        if cert is None:
            return None
        if cert.is_expired and cert.status == SignerStatus.ACTIVE:
            cert.status = SignerStatus.EXPIRED
        return cert.status

    def validate_certificate_chain(
        self, signer_id: str
    ) -> tuple[bool, str | None]:
        """Validate a signer's certificate chain."""
        cert = self._signers.get(signer_id)
        if cert is None:
            return False, f"Signer {signer_id!r} not found"
        if cert.status == SignerStatus.REVOKED:
            return False, f"Signer {signer_id!r} has been revoked"
        if cert.is_expired:
            return False, f"Signer {signer_id!r} certificate has expired"
        if cert.status != SignerStatus.ACTIVE:
            return False, f"Signer {signer_id!r} status is {cert.status.value}"
        return True, None

    def sync_inventory(self) -> SignerInventory:
        """Create a snapshot of the current signer inventory."""
        # Auto-expire any overdue certs
        for cert in self._signers.values():
            if cert.is_expired and cert.status == SignerStatus.ACTIVE:
                cert.status = SignerStatus.EXPIRED
        active = {
            k: v for k, v in self._signers.items() if v.status == SignerStatus.ACTIVE
        }
        inventory = SignerInventory(signers=active)
        logger.info("Synced signer inventory: %d active signers", len(active))
        return inventory

    def get_revocation_list(self) -> list[SignerRevocationEntry]:
        """Get all revocation entries."""
        return list(self._revocations)

    def validate_attestation_against_inventory(
        self, signer_id: str
    ) -> tuple[bool, str | None]:
        """Validate that an attestation's signer is in the live inventory."""
        status = self.check_signer_status(signer_id)
        if status is None:
            return False, f"Signer {signer_id!r} not in inventory"
        if status != SignerStatus.ACTIVE:
            return False, f"Signer {signer_id!r} is {status.value}"
        return True, None

    @property
    def signer_count(self) -> int:
        return len(self._signers)

    @property
    def active_count(self) -> int:
        return sum(1 for c in self._signers.values() if c.is_valid)

    @property
    def revocation_count(self) -> int:
        return len(self._revocations)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_registry: LiveSignerRegistry | None = None


def get_live_signer_registry() -> LiveSignerRegistry:
    """Return the module-level live signer registry."""
    global _registry
    if _registry is None:
        _registry = LiveSignerRegistry()
    return _registry
