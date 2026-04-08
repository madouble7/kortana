"""V15D — Deployment Pipeline Enforcement.

Replaces V14D's simulated promote_with_artifacts with wired deployment
pipeline stages: build → test → scan → approve → stage → canary → production,
with artifact-policy gate enforcement at each stage and automatic rollback
on gate failure.
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

logger = logging.getLogger("kortana.deploy_pipeline_enforcement")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class DeploymentStage(str, Enum):
    """Stages in the deployment pipeline."""

    BUILD = "build"
    TEST = "test"
    SCAN = "scan"
    APPROVE = "approve"
    STAGE = "stage"
    CANARY = "canary"
    PRODUCTION = "production"


STAGE_ORDER = [
    DeploymentStage.BUILD,
    DeploymentStage.TEST,
    DeploymentStage.SCAN,
    DeploymentStage.APPROVE,
    DeploymentStage.STAGE,
    DeploymentStage.CANARY,
    DeploymentStage.PRODUCTION,
]


class GateVerdict(str, Enum):
    """Result of a pipeline gate check."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    PENDING = "pending"


class PipelineStatus(str, Enum):
    """Status of a deployment pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


@dataclass
class PipelineGateConfig:
    """Configuration for a pipeline gate at a specific stage."""

    gate_id: str = field(default_factory=lambda: f"gate_{secrets.token_hex(8)}")
    stage: DeploymentStage = DeploymentStage.BUILD
    required_artifact_types: list[str] = field(default_factory=list)
    require_signer_validation: bool = False
    require_secret_health: bool = False
    max_allowed_vulnerabilities: int = 0
    auto_rollback_on_failure: bool = True
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "stage": self.stage.value,
            "required_artifact_types": self.required_artifact_types,
            "require_signer_validation": self.require_signer_validation,
            "require_secret_health": self.require_secret_health,
            "max_allowed_vulnerabilities": self.max_allowed_vulnerabilities,
            "auto_rollback_on_failure": self.auto_rollback_on_failure,
            "enabled": self.enabled,
        }


@dataclass
class GateCheckResult:
    """Result of evaluating a pipeline gate."""

    check_id: str = field(default_factory=lambda: f"gchk_{secrets.token_hex(8)}")
    gate_id: str = ""
    stage: DeploymentStage = DeploymentStage.BUILD
    version_id: str = ""
    verdict: GateVerdict = GateVerdict.PENDING
    checks_performed: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    check_hash: str = ""

    def __post_init__(self) -> None:
        if not self.check_hash:
            raw = json.dumps(
                {"check_id": self.check_id, "gate_id": self.gate_id,
                 "verdict": self.verdict.value,
                 "ts": self.checked_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.check_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "gate_id": self.gate_id,
            "stage": self.stage.value,
            "version_id": self.version_id,
            "verdict": self.verdict.value,
            "checks_performed": self.checks_performed,
            "failures": self.failures,
            "checked_at": self.checked_at.isoformat(),
            "check_hash": self.check_hash,
        }


@dataclass
class StageExecution:
    """Record of a stage being executed in the pipeline."""

    execution_id: str = field(default_factory=lambda: f"exec_{secrets.token_hex(8)}")
    pipeline_id: str = ""
    stage: DeploymentStage = DeploymentStage.BUILD
    version_id: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    gate_result: GateCheckResult | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "pipeline_id": self.pipeline_id,
            "stage": self.stage.value,
            "version_id": self.version_id,
            "status": self.status.value,
            "gate_result": self.gate_result.to_dict() if self.gate_result else None,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


@dataclass
class RollbackRecord:
    """Record of an automatic rollback triggered by gate failure."""

    rollback_id: str = field(default_factory=lambda: f"rb_{secrets.token_hex(8)}")
    pipeline_id: str = ""
    version_id: str = ""
    failed_stage: DeploymentStage = DeploymentStage.BUILD
    trigger_check_id: str = ""
    reason: str = ""
    rolled_back_at: datetime = field(default_factory=datetime.utcnow)
    rollback_hash: str = ""

    def __post_init__(self) -> None:
        if not self.rollback_hash:
            raw = json.dumps(
                {"rb_id": self.rollback_id, "pipeline": self.pipeline_id,
                 "stage": self.failed_stage.value,
                 "ts": self.rolled_back_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.rollback_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rollback_id": self.rollback_id,
            "pipeline_id": self.pipeline_id,
            "version_id": self.version_id,
            "failed_stage": self.failed_stage.value,
            "trigger_check_id": self.trigger_check_id,
            "reason": self.reason,
            "rolled_back_at": self.rolled_back_at.isoformat(),
            "rollback_hash": self.rollback_hash,
        }


@dataclass
class DeploymentPipeline:
    """Represents a deployment pipeline execution."""

    pipeline_id: str = field(default_factory=lambda: f"pipe_{secrets.token_hex(8)}")
    version_id: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: DeploymentStage = DeploymentStage.BUILD
    stage_executions: list[StageExecution] = field(default_factory=list)
    rollbacks: list[RollbackRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    pipeline_hash: str = ""

    def __post_init__(self) -> None:
        if not self.pipeline_hash:
            raw = json.dumps(
                {"pipe_id": self.pipeline_id, "version": self.version_id,
                 "ts": self.created_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.pipeline_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "version_id": self.version_id,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "stage_count": len(self.stage_executions),
            "rollback_count": len(self.rollbacks),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "pipeline_hash": self.pipeline_hash,
        }


# ---------------------------------------------------------------------------
# Pipeline Enforcer
# ---------------------------------------------------------------------------


class PipelineEnforcer:
    """Enforces artifact-policy gates in the deployment pipeline."""

    def __init__(self) -> None:
        self._gate_configs: dict[DeploymentStage, PipelineGateConfig] = {}
        self._pipelines: dict[str, DeploymentPipeline] = {}
        self._check_history: list[GateCheckResult] = []
        self._rollback_history: list[RollbackRecord] = []

    # -- gate configuration ---------------------------------------------------

    def configure_gate(self, config: PipelineGateConfig) -> PipelineGateConfig:
        """Configure a gate for a pipeline stage."""
        self._gate_configs[config.stage] = config
        logger.info("Configured gate for stage %s", config.stage.value)
        return config

    def get_gate_config(self, stage: DeploymentStage) -> PipelineGateConfig | None:
        return self._gate_configs.get(stage)

    def list_gate_configs(self) -> list[PipelineGateConfig]:
        return list(self._gate_configs.values())

    # -- gate evaluation ------------------------------------------------------

    def evaluate_gate(
        self,
        stage: DeploymentStage,
        version_id: str,
        available_artifacts: list[str] | None = None,
        signer_valid: bool = True,
        secret_health_ok: bool = True,
        vulnerability_count: int = 0,
    ) -> GateCheckResult:
        """Evaluate a pipeline gate for a version."""
        config = self._gate_configs.get(stage)
        if config is None or not config.enabled:
            result = GateCheckResult(
                stage=stage, version_id=version_id,
                verdict=GateVerdict.SKIP,
                checks_performed=["no_gate_configured"],
            )
            self._check_history.append(result)
            return result

        checks_performed: list[str] = []
        failures: list[str] = []
        available = available_artifacts or []

        # Artifact type check
        if config.required_artifact_types:
            checks_performed.append("artifact_types")
            missing = [t for t in config.required_artifact_types if t not in available]
            if missing:
                failures.append(f"Missing artifacts: {', '.join(missing)}")

        # Signer validation check
        if config.require_signer_validation:
            checks_performed.append("signer_validation")
            if not signer_valid:
                failures.append("Signer validation failed")

        # Secret health check
        if config.require_secret_health:
            checks_performed.append("secret_health")
            if not secret_health_ok:
                failures.append("Secret backend health check failed")

        # Vulnerability check
        if config.max_allowed_vulnerabilities >= 0:
            checks_performed.append("vulnerability_scan")
            if vulnerability_count > config.max_allowed_vulnerabilities:
                failures.append(
                    f"Too many vulnerabilities: {vulnerability_count} > {config.max_allowed_vulnerabilities}"
                )

        verdict = GateVerdict.FAIL if failures else GateVerdict.PASS
        result = GateCheckResult(
            gate_id=config.gate_id,
            stage=stage,
            version_id=version_id,
            verdict=verdict,
            checks_performed=checks_performed,
            failures=failures,
        )
        self._check_history.append(result)
        return result

    # -- pipeline execution ---------------------------------------------------

    def create_pipeline(self, version_id: str) -> DeploymentPipeline:
        """Create a new deployment pipeline for a version."""
        pipeline = DeploymentPipeline(version_id=version_id)
        self._pipelines[pipeline.pipeline_id] = pipeline
        logger.info("Created pipeline %s for version %s",
                     pipeline.pipeline_id, version_id)
        return pipeline

    def advance_pipeline(
        self,
        pipeline_id: str,
        available_artifacts: list[str] | None = None,
        signer_valid: bool = True,
        secret_health_ok: bool = True,
        vulnerability_count: int = 0,
    ) -> StageExecution:
        """Advance a pipeline to its next stage, evaluating the gate."""
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            return StageExecution(
                pipeline_id=pipeline_id,
                status=PipelineStatus.FAILED,
                error_message="Pipeline not found",
            )

        if pipeline.status == PipelineStatus.FAILED:
            return StageExecution(
                pipeline_id=pipeline_id,
                stage=pipeline.current_stage,
                version_id=pipeline.version_id,
                status=PipelineStatus.FAILED,
                error_message="Pipeline already failed",
            )

        pipeline.status = PipelineStatus.RUNNING
        stage = pipeline.current_stage

        # Evaluate gate
        gate_result = self.evaluate_gate(
            stage, pipeline.version_id,
            available_artifacts=available_artifacts,
            signer_valid=signer_valid,
            secret_health_ok=secret_health_ok,
            vulnerability_count=vulnerability_count,
        )

        execution = StageExecution(
            pipeline_id=pipeline_id,
            stage=stage,
            version_id=pipeline.version_id,
        )

        if gate_result.verdict == GateVerdict.FAIL:
            execution.status = PipelineStatus.FAILED
            execution.gate_result = gate_result
            execution.completed_at = datetime.utcnow()
            execution.error_message = "; ".join(gate_result.failures)
            pipeline.stage_executions.append(execution)
            pipeline.status = PipelineStatus.FAILED

            # Auto rollback
            gate_config = self._gate_configs.get(stage)
            if gate_config and gate_config.auto_rollback_on_failure:
                rollback = self._trigger_rollback(
                    pipeline, stage, gate_result.check_id,
                    "; ".join(gate_result.failures),
                )
                pipeline.rollbacks.append(rollback)
                pipeline.status = PipelineStatus.ROLLED_BACK

            return execution

        # Gate passed or skipped — advance
        execution.status = PipelineStatus.PASSED
        execution.gate_result = gate_result
        execution.completed_at = datetime.utcnow()
        pipeline.stage_executions.append(execution)

        # Move to next stage
        stage_idx = STAGE_ORDER.index(stage)
        if stage_idx < len(STAGE_ORDER) - 1:
            pipeline.current_stage = STAGE_ORDER[stage_idx + 1]
        else:
            pipeline.status = PipelineStatus.PASSED
            pipeline.completed_at = datetime.utcnow()
            logger.info("Pipeline %s completed: PASSED", pipeline_id)

        return execution

    def _trigger_rollback(
        self,
        pipeline: DeploymentPipeline,
        failed_stage: DeploymentStage,
        check_id: str,
        reason: str,
    ) -> RollbackRecord:
        """Trigger an automatic rollback."""
        rollback = RollbackRecord(
            pipeline_id=pipeline.pipeline_id,
            version_id=pipeline.version_id,
            failed_stage=failed_stage,
            trigger_check_id=check_id,
            reason=reason,
        )
        self._rollback_history.append(rollback)
        logger.warning("Rollback triggered for %s at stage %s: %s",
                        pipeline.pipeline_id, failed_stage.value, reason)
        return rollback

    # -- query ---------------------------------------------------------------

    def get_pipeline(self, pipeline_id: str) -> DeploymentPipeline | None:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> list[DeploymentPipeline]:
        return list(self._pipelines.values())

    def get_check_history(self, version_id: str | None = None) -> list[GateCheckResult]:
        if version_id is None:
            return list(self._check_history)
        return [c for c in self._check_history if c.version_id == version_id]

    def get_rollback_history(self) -> list[RollbackRecord]:
        return list(self._rollback_history)

    @property
    def pipeline_count(self) -> int:
        return len(self._pipelines)

    @property
    def total_checks(self) -> int:
        return len(self._check_history)

    @property
    def total_rollbacks(self) -> int:
        return len(self._rollback_history)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_enforcer: PipelineEnforcer | None = None


def get_pipeline_enforcer() -> PipelineEnforcer:
    """Return the module-level pipeline enforcer."""
    global _enforcer
    if _enforcer is None:
        _enforcer = PipelineEnforcer()
    return _enforcer
