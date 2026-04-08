"""V9 — Quorum overrides, drill schedules/SLOs, audit bundles.

Revision ID: v9a1b2c3d4e5
Revises: v8c1d2e3f4g5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v9a1b2c3d4e5"
down_revision = "v8c1d2e3f4g5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V9A — Quorum approval votes
    op.create_table(
        "quorum_approval",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("override_id", sa.String(32), nullable=False, index=True),
        sa.Column("approver", sa.String(64), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column("audit_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # V9A — Quorum override requests
    op.create_table(
        "quorum_override",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("override_id", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("mode", sa.String(32), nullable=False, index=True),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("requested_by", sa.String(64), nullable=False),
        sa.Column("required_approvals", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending", index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    # V9B — Drill schedules
    op.create_table(
        "drill_schedule",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scenario", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("run_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pass_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fail_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    # V9B — Drill SLOs
    op.create_table(
        "drill_slo",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scenario", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("min_pass_rate", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("lookback_window_minutes", sa.Integer(), nullable=False, server_default="1440"),
        sa.Column("min_runs", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    # V9D — Audit bundles
    op.create_table(
        "audit_bundle",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("bundle_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("from_time", sa.DateTime(), nullable=False),
        sa.Column("to_time", sa.DateTime(), nullable=False),
        sa.Column("generated_by", sa.String(64), nullable=False, server_default="daemon"),
        sa.Column("total_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_overrides", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_drills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_rollbacks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("drill_pass_rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_bundle")
    op.drop_table("drill_slo")
    op.drop_table("drill_schedule")
    op.drop_table("quorum_override")
    op.drop_table("quorum_approval")
