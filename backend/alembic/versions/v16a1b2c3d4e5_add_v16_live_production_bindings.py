"""V16 — live production bindings.

Revision ID: v16a1b2c3d4e5
Revises: v15a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v16a1b2c3d4e5"
down_revision = "v15a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V16A — external call records
    op.create_table(
        "external_call",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("call_id", sa.String(64), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("method", sa.String(8), server_default="GET"),
        sa.Column("status_code", sa.Integer(), server_default="200"),
        sa.Column("outcome", sa.String(32), server_default="success"),
        sa.Column("latency_ms", sa.Float(), server_default="0.0"),
        sa.Column("call_hash", sa.String(64), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
    )

    # V16B — stage transition records
    op.create_table(
        "stage_transition",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("transition_id", sa.String(64), nullable=False),
        sa.Column("pipeline_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("from_stage", sa.String(32), server_default=""),
        sa.Column("to_stage", sa.String(32), nullable=False),
        sa.Column("gate_verdict", sa.String(32), server_default="pass"),
        sa.Column("persistence_status", sa.String(32), server_default="committed"),
        sa.Column("transition_hash", sa.String(64), nullable=True),
        sa.Column("persisted_at", sa.DateTime(), nullable=True),
    )

    # V16B — rollback side-effect records
    op.create_table(
        "rollback_side_effect",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("effect_id", sa.String(64), nullable=False),
        sa.Column("rollback_id", sa.String(64), nullable=False),
        sa.Column("pipeline_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("effect_type", sa.String(32), server_default="config_reverted"),
        sa.Column("affected_resource", sa.String(256), server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("executed", sa.Boolean(), server_default="1"),
        sa.Column("verification_hash", sa.String(64), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
    )

    # V16C — deployment target records
    op.create_table(
        "deployment_target",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("environment", sa.String(32), server_default="staging"),
        sa.Column("endpoint_url", sa.String(512), server_default=""),
        sa.Column("health_check_url", sa.String(512), server_default=""),
        sa.Column("active", sa.Boolean(), server_default="1"),
        sa.Column("target_hash", sa.String(64), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
    )

    # V16D — verification probe records
    op.create_table(
        "verification_probe",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("probe_id", sa.String(64), nullable=False),
        sa.Column("campaign_id", sa.String(64), nullable=False),
        sa.Column("target_system", sa.String(256), nullable=False),
        sa.Column("probe_type", sa.String(32), server_default="version_check"),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("matched", sa.Boolean(), server_default="0"),
        sa.Column("latency_ms", sa.Float(), server_default="0.0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("probe_hash", sa.String(64), nullable=True),
        sa.Column("probed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("verification_probe")
    op.drop_table("deployment_target")
    op.drop_table("rollback_side_effect")
    op.drop_table("stage_transition")
    op.drop_table("external_call")
