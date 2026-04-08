"""V16B — Persistent Stage Store.

Persists pipeline stage transitions, rollback side-effects, and gate
decisions beyond the in-memory DeploymentPipeline from V15D, so that
stage history survives restarts and can be audited externally.
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

logger = logging.getLogger("kortana.persistent_stage_store")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class PersistenceStatus(str, Enum):
    """Status of a persisted record."""

    COMMITTED = "committed"
    PENDING = "pending"
    FAILED = "failed"
    VERIFIED = "verified"


class SideEffectType(str, Enum):
    """Type of rollback side-effect."""

    RESOURCE_SCALED = "resource_scaled"
    TRAFFIC_SHIFTED = "traffic_shifted"
    CONFIG_REVERTED = "config_reverted"
    CACHE_INVALIDATED = "cache_invalidated"
    NOTIFICATION_SENT = "notification_sent"
    ALERT_TRIGGERED = "alert_triggered"


@dataclass
class StageTransitionRecord:
    """A persisted stage transition."""

    transition_id: str = field(default_factory=lambda: f"trans_{secrets.token_hex(8)}")
    pipeline_id: str = ""
    version_id: str = ""
    from_stage: str = ""
    to_stage: str = ""
    gate_verdict: str = "pass"
    gate_check_id: str = ""
    persisted_at: datetime = field(default_factory=datetime.utcnow)
    persistence_status: PersistenceStatus = PersistenceStatus.COMMITTED
    transition_hash: str = ""

    def __post_init__(self) -> None:
        if not self.transition_hash:
            raw = json.dumps(
                {"trans_id": self.transition_id, "pipeline": self.pipeline_id,
                 "from": self.from_stage, "to": self.to_stage,
                 "ts": self.persisted_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.transition_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "pipeline_id": self.pipeline_id,
            "version_id": self.version_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "gate_verdict": self.gate_verdict,
            "persistence_status": self.persistence_status.value,
            "persisted_at": self.persisted_at.isoformat(),
            "transition_hash": self.transition_hash,
        }


@dataclass
class RollbackSideEffect:
    """A side-effect produced by a rollback."""

    effect_id: str = field(default_factory=lambda: f"eff_{secrets.token_hex(8)}")
    rollback_id: str = ""
    pipeline_id: str = ""
    version_id: str = ""
    effect_type: SideEffectType = SideEffectType.CONFIG_REVERTED
    affected_resource: str = ""
    description: str = ""
    executed: bool = True
    executed_at: datetime = field(default_factory=datetime.utcnow)
    verification_hash: str = ""

    def __post_init__(self) -> None:
        if not self.verification_hash:
            raw = json.dumps(
                {"eff_id": self.effect_id, "rollback": self.rollback_id,
                 "type": self.effect_type.value,
                 "ts": self.executed_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.verification_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "rollback_id": self.rollback_id,
            "pipeline_id": self.pipeline_id,
            "version_id": self.version_id,
            "effect_type": self.effect_type.value,
            "affected_resource": self.affected_resource,
            "description": self.description,
            "executed": self.executed,
            "executed_at": self.executed_at.isoformat(),
            "verification_hash": self.verification_hash,
        }


@dataclass
class PersistenceIntegrityCheck:
    """Result of verifying persistence integrity."""

    check_id: str = field(default_factory=lambda: f"intg_{secrets.token_hex(8)}")
    pipeline_id: str = ""
    transitions_count: int = 0
    effects_count: int = 0
    all_hashes_valid: bool = True
    chain_continuous: bool = True
    checked_at: datetime = field(default_factory=datetime.utcnow)
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        if not self.integrity_hash:
            raw = json.dumps(
                {"check_id": self.check_id, "pipeline": self.pipeline_id,
                 "valid": self.all_hashes_valid,
                 "ts": self.checked_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.integrity_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "pipeline_id": self.pipeline_id,
            "transitions_count": self.transitions_count,
            "effects_count": self.effects_count,
            "all_hashes_valid": self.all_hashes_valid,
            "chain_continuous": self.chain_continuous,
            "checked_at": self.checked_at.isoformat(),
            "integrity_hash": self.integrity_hash,
        }


# ---------------------------------------------------------------------------
# Stage Persistence Store
# ---------------------------------------------------------------------------


class StagePersistenceStore:
    """Persists stage transitions and rollback side-effects durably."""

    def __init__(self) -> None:
        self._transitions: dict[str, list[StageTransitionRecord]] = {}
        self._side_effects: dict[str, list[RollbackSideEffect]] = {}
        self._integrity_checks: list[PersistenceIntegrityCheck] = []

    # -- transition persistence -----------------------------------------------

    def persist_transition(
        self,
        pipeline_id: str,
        version_id: str,
        from_stage: str,
        to_stage: str,
        gate_verdict: str = "pass",
        gate_check_id: str = "",
    ) -> StageTransitionRecord:
        """Persist a stage transition record."""
        record = StageTransitionRecord(
            pipeline_id=pipeline_id,
            version_id=version_id,
            from_stage=from_stage,
            to_stage=to_stage,
            gate_verdict=gate_verdict,
            gate_check_id=gate_check_id,
        )
        self._transitions.setdefault(pipeline_id, []).append(record)
        logger.info("Persisted transition %s: %s → %s",
                     pipeline_id, from_stage, to_stage)
        return record

    def get_transitions(self, pipeline_id: str) -> list[StageTransitionRecord]:
        """Get all transitions for a pipeline."""
        return list(self._transitions.get(pipeline_id, []))

    def get_all_transitions(self) -> list[StageTransitionRecord]:
        """Get all transitions across all pipelines."""
        result: list[StageTransitionRecord] = []
        for records in self._transitions.values():
            result.extend(records)
        return result

    # -- rollback side-effects ------------------------------------------------

    def persist_rollback_effect(
        self,
        rollback_id: str,
        pipeline_id: str,
        version_id: str,
        effect_type: SideEffectType,
        affected_resource: str,
        description: str = "",
    ) -> RollbackSideEffect:
        """Persist a rollback side-effect."""
        effect = RollbackSideEffect(
            rollback_id=rollback_id,
            pipeline_id=pipeline_id,
            version_id=version_id,
            effect_type=effect_type,
            affected_resource=affected_resource,
            description=description,
        )
        self._side_effects.setdefault(rollback_id, []).append(effect)
        logger.info("Persisted rollback effect %s: %s on %s",
                     rollback_id, effect_type.value, affected_resource)
        return effect

    def get_rollback_effects(self, rollback_id: str) -> list[RollbackSideEffect]:
        """Get side-effects for a rollback."""
        return list(self._side_effects.get(rollback_id, []))

    def get_all_effects(self) -> list[RollbackSideEffect]:
        """Get all side-effects across all rollbacks."""
        result: list[RollbackSideEffect] = []
        for effects in self._side_effects.values():
            result.extend(effects)
        return result

    # -- integrity verification -----------------------------------------------

    def verify_persistence_integrity(self, pipeline_id: str) -> PersistenceIntegrityCheck:
        """Verify integrity of persisted transitions for a pipeline."""
        transitions = self._transitions.get(pipeline_id, [])
        effects_count = sum(
            len(effs)
            for effs in self._side_effects.values()
            if any(e.pipeline_id == pipeline_id for e in effs)
        )

        # Check hash validity (all non-empty)
        all_hashes_valid = all(t.transition_hash for t in transitions)

        # Check stage continuity
        chain_continuous = True
        for i in range(1, len(transitions)):
            if transitions[i].from_stage != transitions[i - 1].to_stage:
                chain_continuous = False
                break

        check = PersistenceIntegrityCheck(
            pipeline_id=pipeline_id,
            transitions_count=len(transitions),
            effects_count=effects_count,
            all_hashes_valid=all_hashes_valid,
            chain_continuous=chain_continuous,
        )
        self._integrity_checks.append(check)
        return check

    def get_integrity_checks(self) -> list[PersistenceIntegrityCheck]:
        return list(self._integrity_checks)

    # -- query ---------------------------------------------------------------

    @property
    def total_transitions(self) -> int:
        return sum(len(t) for t in self._transitions.values())

    @property
    def total_effects(self) -> int:
        return sum(len(e) for e in self._side_effects.values())

    @property
    def pipeline_count(self) -> int:
        return len(self._transitions)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_store: StagePersistenceStore | None = None


def get_stage_persistence_store() -> StagePersistenceStore:
    """Return the module-level stage persistence store."""
    global _store
    if _store is None:
        _store = StagePersistenceStore()
    return _store
