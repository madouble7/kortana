"""V17D — Evidence Chain.

A cryptographic chain of evidence showing not just that the control plane
decided something, but that the outside world converged to that decision.
Each entry links to the previous via hash, creating an immutable audit
trail from decision → deployment → observation → convergence.
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

logger = logging.getLogger("kortana.evidence_chain")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EvidenceType(str, Enum):
    """Type of evidence entry."""

    DECISION = "decision"
    DEPLOYMENT = "deployment"
    OBSERVATION = "observation"
    CONVERGENCE = "convergence"
    ROLLBACK = "rollback"
    ESCALATION = "escalation"
    VERIFICATION = "verification"


class ChainStatus(str, Enum):
    """Status of an evidence chain."""

    OPEN = "open"
    SEALED = "sealed"
    VERIFIED = "verified"
    TAMPERED = "tampered"


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------


@dataclass
class EvidenceEntry:
    """A single entry in the evidence chain."""

    entry_id: str = field(default_factory=lambda: f"ev_{secrets.token_hex(8)}")
    chain_id: str = ""
    sequence: int = 0
    evidence_type: EvidenceType = EvidenceType.DECISION
    actor: str = ""
    description: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    entry_hash: str = ""

    def compute_hash(self) -> str:
        """Compute the hash for this entry (including previous_hash for chaining)."""
        raw = json.dumps(
            {"entry_id": self.entry_id, "chain_id": self.chain_id,
             "seq": self.sequence,
             "type": self.evidence_type.value,
             "actor": self.actor,
             "payload": self.payload,
             "prev": self.previous_hash,
             "ts": self.created_at.isoformat()},
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def __post_init__(self) -> None:
        if not self.entry_hash:
            self.entry_hash = self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "chain_id": self.chain_id,
            "sequence": self.sequence,
            "evidence_type": self.evidence_type.value,
            "actor": self.actor,
            "description": self.description,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ConvergenceProof:
    """Proof that external world converged to a decision."""

    proof_id: str = field(default_factory=lambda: f"proof_{secrets.token_hex(8)}")
    chain_id: str = ""
    version_id: str = ""
    decision_entry_id: str = ""
    deployment_entry_id: str = ""
    observation_entry_ids: list[str] = field(default_factory=list)
    convergence_entry_id: str = ""
    all_stages_present: bool = True
    chain_integrity: bool = True
    proof_hash: str = ""

    def __post_init__(self) -> None:
        if not self.proof_hash:
            raw = json.dumps(
                {"proof": self.proof_id, "chain": self.chain_id,
                 "version": self.version_id,
                 "stages": self.all_stages_present,
                 "integrity": self.chain_integrity},
                sort_keys=True, separators=(",", ":"),
            )
            self.proof_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def is_valid(self) -> bool:
        return self.all_stages_present and self.chain_integrity

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "chain_id": self.chain_id,
            "version_id": self.version_id,
            "decision_entry_id": self.decision_entry_id,
            "deployment_entry_id": self.deployment_entry_id,
            "observation_entry_ids": self.observation_entry_ids,
            "convergence_entry_id": self.convergence_entry_id,
            "all_stages_present": self.all_stages_present,
            "chain_integrity": self.chain_integrity,
            "is_valid": self.is_valid,
            "proof_hash": self.proof_hash,
        }


# ---------------------------------------------------------------------------
# Evidence Chain
# ---------------------------------------------------------------------------


class EvidenceChain:
    """An ordered, hash-linked chain of evidence entries."""

    def __init__(self, chain_id: str = "", version_id: str = "", description: str = "") -> None:
        self.chain_id = chain_id or f"chain_{secrets.token_hex(8)}"
        self.version_id = version_id
        self.description = description
        self.entries: list[EvidenceEntry] = []
        self.status: ChainStatus = ChainStatus.OPEN
        self.created_at: datetime = datetime.utcnow()
        self.sealed_at: datetime | None = None

    def append_entry(
        self,
        evidence_type: EvidenceType,
        actor: str,
        description: str = "",
        payload: dict[str, Any] | None = None,
    ) -> EvidenceEntry:
        """Append a new entry to the chain."""
        if self.status != ChainStatus.OPEN:
            raise ValueError(f"Cannot append to {self.status.value} chain")

        previous_hash = self.entries[-1].entry_hash if self.entries else ""
        entry = EvidenceEntry(
            chain_id=self.chain_id,
            sequence=len(self.entries),
            evidence_type=evidence_type,
            actor=actor,
            description=description,
            payload=payload or {},
            previous_hash=previous_hash,
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> tuple[bool, str]:
        """Verify the integrity of the hash chain."""
        if not self.entries:
            return True, "Empty chain"

        # First entry should have empty previous_hash
        if self.entries[0].previous_hash != "":
            return False, "First entry has non-empty previous_hash"

        for i in range(1, len(self.entries)):
            expected_prev = self.entries[i - 1].entry_hash
            if self.entries[i].previous_hash != expected_prev:
                return False, f"Chain broken at entry {i}: expected prev={expected_prev[:16]}..."
            # Verify entry hash
            recomputed = self.entries[i].compute_hash()
            if self.entries[i].entry_hash != recomputed:
                return False, f"Entry {i} hash mismatch"

        return True, f"Chain valid ({len(self.entries)} entries)"

    def seal(self) -> None:
        """Seal the chain — no more entries can be added."""
        self.status = ChainStatus.SEALED
        self.sealed_at = datetime.utcnow()

    def get_convergence_proof(self) -> ConvergenceProof:
        """Generate a convergence proof from the chain."""
        decision_id = ""
        deployment_id = ""
        observation_ids: list[str] = []
        convergence_id = ""

        for entry in self.entries:
            if entry.evidence_type == EvidenceType.DECISION and not decision_id:
                decision_id = entry.entry_id
            elif entry.evidence_type == EvidenceType.DEPLOYMENT and not deployment_id:
                deployment_id = entry.entry_id
            elif entry.evidence_type == EvidenceType.OBSERVATION:
                observation_ids.append(entry.entry_id)
            elif entry.evidence_type == EvidenceType.CONVERGENCE and not convergence_id:
                convergence_id = entry.entry_id

        all_stages = bool(decision_id and deployment_id and observation_ids and convergence_id)
        chain_ok, _ = self.verify_chain()

        return ConvergenceProof(
            chain_id=self.chain_id,
            version_id=self.version_id,
            decision_entry_id=decision_id,
            deployment_entry_id=deployment_id,
            observation_entry_ids=observation_ids,
            convergence_entry_id=convergence_id,
            all_stages_present=all_stages,
            chain_integrity=chain_ok,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "version_id": self.version_id,
            "description": self.description,
            "status": self.status.value,
            "entry_count": len(self.entries),
            "created_at": self.created_at.isoformat(),
            "sealed_at": self.sealed_at.isoformat() if self.sealed_at else None,
        }


# ---------------------------------------------------------------------------
# Evidence Chain Registry
# ---------------------------------------------------------------------------


class EvidenceChainRegistry:
    """Manages evidence chains."""

    def __init__(self) -> None:
        self._chains: dict[str, EvidenceChain] = {}

    def create_chain(
        self,
        version_id: str,
        description: str = "",
    ) -> EvidenceChain:
        """Create a new evidence chain."""
        chain = EvidenceChain(version_id=version_id, description=description)
        self._chains[chain.chain_id] = chain
        logger.info("Created evidence chain %s for version %s",
                     chain.chain_id, version_id)
        return chain

    def get_chain(self, chain_id: str) -> EvidenceChain | None:
        return self._chains.get(chain_id)

    def seal_chain(self, chain_id: str) -> EvidenceChain | None:
        """Seal a chain."""
        chain = self._chains.get(chain_id)
        if chain:
            chain.seal()
            ok, _ = chain.verify_chain()
            chain.status = ChainStatus.VERIFIED if ok else ChainStatus.TAMPERED
        return chain

    def verify_chain(self, chain_id: str) -> tuple[bool, str]:
        """Verify a chain\'s integrity."""
        chain = self._chains.get(chain_id)
        if chain is None:
            return False, "Chain not found"
        return chain.verify_chain()

    def verify_all(self) -> dict[str, tuple[bool, str]]:
        """Verify all chains."""
        return {cid: chain.verify_chain() for cid, chain in self._chains.items()}

    def get_chains(
        self,
        version_id: str = "",
        status: ChainStatus | None = None,
    ) -> list[EvidenceChain]:
        chains = list(self._chains.values())
        if version_id:
            chains = [c for c in chains if c.version_id == version_id]
        if status:
            chains = [c for c in chains if c.status == status]
        return chains

    def get_convergence_proof(self, chain_id: str) -> ConvergenceProof | None:
        chain = self._chains.get(chain_id)
        if chain is None:
            return None
        return chain.get_convergence_proof()

    @property
    def chain_count(self) -> int:
        return len(self._chains)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_registry: EvidenceChainRegistry | None = None


def get_evidence_chain_registry() -> EvidenceChainRegistry:
    """Return the module-level evidence chain registry."""
    global _registry
    if _registry is None:
        _registry = EvidenceChainRegistry()
    return _registry
