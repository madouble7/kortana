"""V13C — Signed Webhook & CI Attestation.

Signs outbound webhooks with HMAC-SHA256 for integrity and verifies
inbound CI attestation payloads.  An ``AttestationChain`` provides
tamper-evident ordering of attestation records.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.webhook_attestation")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class AttestationType(str, Enum):
    """Types of attestation payload."""

    WEBHOOK_SIGNATURE = "webhook_signature"
    CI_PIPELINE = "ci_pipeline"
    DEPLOY_RECEIPT = "deploy_receipt"
    AUDIT_SEAL = "audit_seal"


@dataclass
class AttestationPayload:
    """An attestation record with cryptographic integrity."""

    attestation_id: str = field(
        default_factory=lambda: f"att_{secrets.token_hex(8)}"
    )
    attestation_type: AttestationType = AttestationType.WEBHOOK_SIGNATURE
    subject: str = ""
    claims: dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    signer_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload_hash: str = ""

    def __post_init__(self) -> None:
        if not self.payload_hash:
            self.payload_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "attestation_id": self.attestation_id,
                "subject": self.subject,
                "signer_id": self.signer_id,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "attestation_type": self.attestation_type.value,
            "subject": self.subject,
            "claims": self.claims,
            "signature": self.signature,
            "signer_id": self.signer_id,
            "timestamp": self.timestamp.isoformat(),
            "payload_hash": self.payload_hash,
        }


# ---------------------------------------------------------------------------
# Webhook signing
# ---------------------------------------------------------------------------


class WebhookSigner:
    """HMAC-SHA256 signer for webhook payloads."""

    @staticmethod
    def sign(payload_bytes: bytes, secret: str) -> str:
        """Sign ``payload_bytes`` with ``secret`` and return hex digest."""
        return hmac.new(
            secret.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify(payload_bytes: bytes, signature: str, secret: str) -> bool:
        """Verify an HMAC-SHA256 signature."""
        expected = hmac.new(
            secret.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# CI attestation verifier
# ---------------------------------------------------------------------------


class CIAttestationVerifier:
    """Manages trusted signers and verifies CI attestation payloads."""

    def __init__(self) -> None:
        self._trusted_signers: dict[str, str] = {}  # signer_id -> shared_secret
        self._verified: list[AttestationPayload] = []

    def register_trusted_signer(self, signer_id: str, key: str) -> None:
        """Register a signer as trusted with their shared secret."""
        self._trusted_signers[signer_id] = key
        logger.info("Registered trusted signer: %s", signer_id)

    def verify_attestation(
        self, attestation: AttestationPayload
    ) -> tuple[bool, str | None]:
        """Verify an attestation payload.

        Checks that the signer is trusted and the signature is valid.
        """
        if attestation.signer_id not in self._trusted_signers:
            return False, f"Signer {attestation.signer_id!r} is not trusted"

        secret = self._trusted_signers[attestation.signer_id]
        payload_bytes = attestation.payload_hash.encode()
        if not WebhookSigner.verify(payload_bytes, attestation.signature, secret):
            return False, "Signature verification failed"

        self._verified.append(attestation)
        logger.info(
            "Verified attestation: id=%s signer=%s",
            attestation.attestation_id,
            attestation.signer_id,
        )
        return True, None

    def list_trusted_signers(self) -> list[str]:
        """Return list of trusted signer IDs."""
        return list(self._trusted_signers.keys())

    @property
    def verified_count(self) -> int:
        return len(self._verified)

    @property
    def signer_count(self) -> int:
        return len(self._trusted_signers)


# ---------------------------------------------------------------------------
# Attestation chain
# ---------------------------------------------------------------------------


class AttestationChain:
    """Tamper-evident chain of attestation records."""

    def __init__(self) -> None:
        self._chain: list[AttestationPayload] = []

    def append(self, attestation: AttestationPayload) -> None:
        """Append an attestation to the chain."""
        self._chain.append(attestation)
        logger.info(
            "Chain append: id=%s (length=%d)",
            attestation.attestation_id,
            len(self._chain),
        )

    def verify_chain(self) -> tuple[bool, str | None]:
        """Verify all entries in the chain have valid payload hashes."""
        for i, entry in enumerate(self._chain):
            expected = entry._compute_hash()
            if entry.payload_hash != expected:
                return False, (
                    f"Chain entry {i} ({entry.attestation_id}) "
                    f"hash mismatch: expected {expected}, got {entry.payload_hash}"
                )
        return True, None

    def get_chain(self) -> list[AttestationPayload]:
        """Return the full chain."""
        return list(self._chain)

    @property
    def chain_length(self) -> int:
        return len(self._chain)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_verifier: CIAttestationVerifier | None = None


def get_attestation_verifier() -> CIAttestationVerifier:
    """Return the module-level CI attestation verifier."""
    global _verifier
    if _verifier is None:
        _verifier = CIAttestationVerifier()
    return _verifier
