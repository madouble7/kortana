"""V9D — Audit Bundle: exportable audit packages for incidents and reviews.

Gathers all policy decisions, overrides, drills, rollbacks, and policy
versions within a time window into a single structured bundle.
Supports JSON serialisation and human-readable Markdown rendering.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.audit_bundle")


# ---------------------------------------------------------------------------
# Audit bundle
# ---------------------------------------------------------------------------


@dataclass
class AuditBundle:
    """A packaged snapshot of all audit-relevant data within a time window."""

    bundle_id: str
    from_time: str
    to_time: str
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    generated_by: str = "daemon"

    # Collections
    decisions: list[dict[str, Any]] = field(default_factory=list)
    overrides: list[dict[str, Any]] = field(default_factory=list)
    quorum_overrides: list[dict[str, Any]] = field(default_factory=list)
    drills: list[dict[str, Any]] = field(default_factory=list)
    rollbacks: list[dict[str, Any]] = field(default_factory=list)
    policy_versions: list[dict[str, Any]] = field(default_factory=list)

    # Summary
    total_decisions: int = 0
    total_overrides: int = 0
    total_drills: int = 0
    total_rollbacks: int = 0
    drill_pass_rate: float = 1.0
    content_hash: str = ""

    def compute_hash(self) -> str:
        """SHA-256 over the bundle content for integrity verification."""
        payload = json.dumps(
            {
                "bundle_id": self.bundle_id,
                "from_time": self.from_time,
                "to_time": self.to_time,
                "decisions": self.decisions,
                "overrides": self.overrides,
                "quorum_overrides": self.quorum_overrides,
                "drills": self.drills,
                "rollbacks": self.rollbacks,
                "policy_versions": self.policy_versions,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def finalize(self) -> None:
        """Compute summary statistics and content hash."""
        self.total_decisions = len(self.decisions)
        self.total_overrides = len(self.overrides)
        self.total_drills = len(self.drills)
        self.total_rollbacks = len(self.rollbacks)

        if self.drills:
            passed = sum(1 for d in self.drills if d.get("passed"))
            self.drill_pass_rate = passed / len(self.drills)
        else:
            self.drill_pass_rate = 1.0

        self.content_hash = self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "from_time": self.from_time,
            "to_time": self.to_time,
            "generated_at": self.generated_at,
            "generated_by": self.generated_by,
            "summary": {
                "total_decisions": self.total_decisions,
                "total_overrides": self.total_overrides,
                "total_drills": self.total_drills,
                "total_rollbacks": self.total_rollbacks,
                "drill_pass_rate": round(self.drill_pass_rate, 4),
            },
            "decisions": self.decisions,
            "overrides": self.overrides,
            "quorum_overrides": self.quorum_overrides,
            "drills": self.drills,
            "rollbacks": self.rollbacks,
            "policy_versions": self.policy_versions,
            "content_hash": self.content_hash,
        }


# ---------------------------------------------------------------------------
# Bundle builder (from in-memory or DB data)
# ---------------------------------------------------------------------------


def build_audit_bundle(
    bundle_id: str,
    from_time: datetime,
    to_time: datetime,
    *,
    decisions: list[dict[str, Any]] | None = None,
    overrides: list[dict[str, Any]] | None = None,
    quorum_overrides: list[dict[str, Any]] | None = None,
    drills: list[dict[str, Any]] | None = None,
    rollbacks: list[dict[str, Any]] | None = None,
    policy_versions: list[dict[str, Any]] | None = None,
    generated_by: str = "daemon",
) -> AuditBundle:
    """Build and finalize an audit bundle from provided data."""

    def _filter_by_time(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for r in records:
            created = r.get("created_at")
            if created is None:
                result.append(r)
                continue
            if isinstance(created, str):
                try:
                    created = datetime.fromisoformat(created)
                except ValueError:
                    result.append(r)
                    continue
            if from_time <= created <= to_time:
                result.append(r)
        return result

    bundle = AuditBundle(
        bundle_id=bundle_id,
        from_time=from_time.isoformat(),
        to_time=to_time.isoformat(),
        generated_by=generated_by,
        decisions=_filter_by_time(decisions or []),
        overrides=_filter_by_time(overrides or []),
        quorum_overrides=quorum_overrides or [],
        drills=_filter_by_time(drills or []),
        rollbacks=_filter_by_time(rollbacks or []),
        policy_versions=_filter_by_time(policy_versions or []),
    )
    bundle.finalize()
    return bundle


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def render_bundle_markdown(bundle: AuditBundle) -> str:
    """Render an audit bundle as human-readable Markdown."""

    lines: list[str] = []
    lines.append(f"# Audit Bundle: {bundle.bundle_id}")
    lines.append("")
    lines.append(f"**Window:** {bundle.from_time} → {bundle.to_time}")
    lines.append(f"**Generated:** {bundle.generated_at} by {bundle.generated_by}")
    lines.append(f"**Content Hash:** `{bundle.content_hash}`")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Policy Decisions | {bundle.total_decisions} |")
    lines.append(f"| Human Overrides | {bundle.total_overrides} |")
    lines.append(f"| Chaos Drills | {bundle.total_drills} |")
    lines.append(f"| Rollbacks | {bundle.total_rollbacks} |")
    lines.append(f"| Drill Pass Rate | {bundle.drill_pass_rate:.1%} |")
    lines.append("")

    # Decisions
    if bundle.decisions:
        lines.append("## Policy Decisions")
        lines.append("")
        lines.append("| Time | Type | Actor | Action | From → To | Hash |")
        lines.append("|------|------|-------|--------|-----------|------|")
        for d in bundle.decisions:
            ts = d.get("created_at", "?")
            lines.append(
                f"| {ts} | {d.get('decision_type', '?')} | "
                f"{d.get('actor', '?')} | {d.get('action', '?')} | "
                f"{d.get('from_state', '?')} → {d.get('to_state', '?')} | "
                f"`{str(d.get('audit_hash', '?'))[:12]}` |"
            )
        lines.append("")

    # Overrides
    if bundle.overrides:
        lines.append("## Human Overrides")
        lines.append("")
        for o in bundle.overrides:
            status = "REVOKED" if o.get("revoked") else "ACTIVE"
            lines.append(
                f"- **{o.get('mode', '?')}** by {o.get('created_by', '?')} "
                f"({status}) — {o.get('reason', '?')}"
            )
        lines.append("")

    # Drills
    if bundle.drills:
        lines.append("## Chaos Drills")
        lines.append("")
        lines.append("| Time | Scenario | Result | Duration |")
        lines.append("|------|----------|--------|----------|")
        for d in bundle.drills:
            result = "✅ PASS" if d.get("passed") else "❌ FAIL"
            lines.append(
                f"| {d.get('created_at', '?')} | {d.get('scenario', '?')} | "
                f"{result} | {d.get('duration_ms', 0)}ms |"
            )
        lines.append("")

    # Rollbacks
    if bundle.rollbacks:
        lines.append("## Rollbacks")
        lines.append("")
        for r in bundle.rollbacks:
            lines.append(
                f"- **{r.get('trigger', '?')}**: "
                f"{r.get('from_mode', '?')} → {r.get('to_mode', '?')} "
                f"at {r.get('created_at', '?')}"
            )
        lines.append("")

    # Policy versions
    if bundle.policy_versions:
        lines.append("## Policy Versions")
        lines.append("")
        for pv in bundle.policy_versions:
            lines.append(
                f"- **v{pv.get('version', '?')}** by {pv.get('created_by', '?')} "
                f"at {pv.get('created_at', '?')} — hash `{str(pv.get('content_hash', '?'))[:12]}`"
            )
        lines.append("")

    return "\n".join(lines)
