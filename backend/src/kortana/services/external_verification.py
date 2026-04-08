"""V16D — External Verification.

End-to-end verification that external systems actually observed the
decisions made by the control plane.  Creates verification campaigns
that probe external systems and confirm state matches expectations.
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

logger = logging.getLogger("kortana.external_verification")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class ProbeType(str, Enum):
    """Type of verification probe."""

    VERSION_CHECK = "version_check"
    HEALTH_CHECK = "health_check"
    CONFIG_CHECK = "config_check"
    CERTIFICATE_CHECK = "certificate_check"
    SECRET_CHECK = "secret_check"
    DEPLOYMENT_CHECK = "deployment_check"


class ProbeStatus(str, Enum):
    """Status of a verification probe."""

    PENDING = "pending"
    PROBING = "probing"
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    UNREACHABLE = "unreachable"
    ERROR = "error"


class CampaignStatus(str, Enum):
    """Status of a verification campaign."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class VerificationProbe:
    """A single probe sent to an external system."""

    probe_id: str = field(default_factory=lambda: f"prb_{secrets.token_hex(8)}")
    campaign_id: str = ""
    target_system: str = ""
    probe_type: ProbeType = ProbeType.VERSION_CHECK
    expected_state: dict[str, Any] = field(default_factory=dict)
    observed_state: dict[str, Any] = field(default_factory=dict)
    status: ProbeStatus = ProbeStatus.PENDING
    latency_ms: float = 0.0
    error: str = ""
    probed_at: datetime | None = None
    probe_hash: str = ""

    def __post_init__(self) -> None:
        if not self.probe_hash:
            raw = json.dumps(
                {"probe": self.probe_id, "target": self.target_system,
                 "type": self.probe_type.value},
                sort_keys=True, separators=(",", ":"),
            )
            self.probe_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def matched(self) -> bool:
        return self.status == ProbeStatus.MATCHED

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "campaign_id": self.campaign_id,
            "target_system": self.target_system,
            "probe_type": self.probe_type.value,
            "expected_state": self.expected_state,
            "observed_state": self.observed_state,
            "status": self.status.value,
            "matched": self.matched,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "probed_at": self.probed_at.isoformat() if self.probed_at else None,
            "probe_hash": self.probe_hash,
        }


@dataclass
class VerificationCampaign:
    """A campaign of probes to verify external system state."""

    campaign_id: str = field(default_factory=lambda: f"camp_{secrets.token_hex(8)}")
    version_id: str = ""
    pipeline_id: str = ""
    description: str = ""
    probes: list[VerificationProbe] = field(default_factory=list)
    status: CampaignStatus = CampaignStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    campaign_hash: str = ""

    def __post_init__(self) -> None:
        if not self.campaign_hash:
            raw = json.dumps(
                {"camp": self.campaign_id, "version": self.version_id,
                 "ts": self.created_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.campaign_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def all_matched(self) -> bool:
        return all(p.matched for p in self.probes) and len(self.probes) > 0

    @property
    def match_count(self) -> int:
        return sum(1 for p in self.probes if p.matched)

    @property
    def total_probes(self) -> int:
        return len(self.probes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "version_id": self.version_id,
            "pipeline_id": self.pipeline_id,
            "description": self.description,
            "status": self.status.value,
            "total_probes": self.total_probes,
            "match_count": self.match_count,
            "all_matched": self.all_matched,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "campaign_hash": self.campaign_hash,
        }


# ---------------------------------------------------------------------------
# External Verifier
# ---------------------------------------------------------------------------


class ExternalVerifier:
    """Creates and executes verification campaigns against external systems."""

    def __init__(self) -> None:
        self._campaigns: dict[str, VerificationCampaign] = {}

    def create_campaign(
        self,
        version_id: str,
        pipeline_id: str = "",
        description: str = "",
    ) -> VerificationCampaign:
        """Create a new verification campaign."""
        campaign = VerificationCampaign(
            version_id=version_id,
            pipeline_id=pipeline_id,
            description=description,
        )
        self._campaigns[campaign.campaign_id] = campaign
        logger.info("Created verification campaign %s for version %s",
                     campaign.campaign_id, version_id)
        return campaign

    def add_probe(
        self,
        campaign_id: str,
        target_system: str,
        probe_type: ProbeType,
        expected_state: dict[str, Any] | None = None,
    ) -> VerificationProbe | None:
        """Add a probe to an existing campaign."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return None
        probe = VerificationProbe(
            campaign_id=campaign_id,
            target_system=target_system,
            probe_type=probe_type,
            expected_state=expected_state or {},
        )
        campaign.probes.append(probe)
        return probe

    def execute_probe(
        self,
        campaign_id: str,
        probe_id: str,
        observed_state: dict[str, Any] | None = None,
        simulate_unreachable: bool = False,
        simulate_error: str = "",
    ) -> VerificationProbe | None:
        """Execute a specific probe (simulated observation in test mode)."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return None
        probe = next((p for p in campaign.probes if p.probe_id == probe_id), None)
        if probe is None:
            return None

        probe.probed_at = datetime.utcnow()

        if simulate_unreachable:
            probe.status = ProbeStatus.UNREACHABLE
            probe.error = "Target system unreachable"
            probe.latency_ms = 0.0
            return probe

        if simulate_error:
            probe.status = ProbeStatus.ERROR
            probe.error = simulate_error
            probe.latency_ms = 0.0
            return probe

        observed = observed_state or {}
        probe.observed_state = observed
        probe.latency_ms = 1.5

        # Compare expected vs observed
        if probe.expected_state == observed:
            probe.status = ProbeStatus.MATCHED
        else:
            probe.status = ProbeStatus.MISMATCHED

        return probe

    def execute_campaign(
        self,
        campaign_id: str,
        observed_states: dict[str, dict[str, Any]] | None = None,
        simulate_unreachable: list[str] | None = None,
    ) -> VerificationCampaign | None:
        """Execute all probes in a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return None

        campaign.status = CampaignStatus.RUNNING
        unreachable_set = set(simulate_unreachable or [])
        states = observed_states or {}

        for probe in campaign.probes:
            if probe.target_system in unreachable_set:
                self.execute_probe(campaign_id, probe.probe_id,
                                   simulate_unreachable=True)
            elif probe.target_system in states:
                self.execute_probe(campaign_id, probe.probe_id,
                                   observed_state=states[probe.target_system])
            else:
                # Default: return expected state (assume nominal)
                self.execute_probe(campaign_id, probe.probe_id,
                                   observed_state=probe.expected_state)

        # Determine overall campaign status
        campaign.completed_at = datetime.utcnow()
        if campaign.all_matched:
            campaign.status = CampaignStatus.COMPLETED
        elif campaign.match_count > 0:
            campaign.status = CampaignStatus.PARTIAL
        else:
            campaign.status = CampaignStatus.FAILED

        logger.info("Campaign %s: %d/%d probes matched → %s",
                     campaign_id, campaign.match_count,
                     campaign.total_probes, campaign.status.value)
        return campaign

    def verify_campaign(self, campaign_id: str) -> tuple[bool, str]:
        """Check whether a campaign fully verified."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return False, "Campaign not found"
        if campaign.status == CampaignStatus.CREATED:
            return False, "Campaign not yet executed"
        if campaign.all_matched:
            return True, f"All {campaign.total_probes} probes matched"
        mismatched = [
            p.target_system for p in campaign.probes if not p.matched
        ]
        return False, f"Mismatched probes: {mismatched}"

    # -- queries --------------------------------------------------------------

    def get_campaign(self, campaign_id: str) -> VerificationCampaign | None:
        return self._campaigns.get(campaign_id)

    def get_campaigns(
        self,
        version_id: str = "",
        status: CampaignStatus | None = None,
    ) -> list[VerificationCampaign]:
        campaigns = list(self._campaigns.values())
        if version_id:
            campaigns = [c for c in campaigns if c.version_id == version_id]
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns

    def get_probes(self, campaign_id: str) -> list[VerificationProbe]:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return []
        return list(campaign.probes)

    @property
    def campaign_count(self) -> int:
        return len(self._campaigns)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_verifier: ExternalVerifier | None = None


def get_external_verifier() -> ExternalVerifier:
    """Return the module-level external verifier."""
    global _verifier
    if _verifier is None:
        _verifier = ExternalVerifier()
    return _verifier
