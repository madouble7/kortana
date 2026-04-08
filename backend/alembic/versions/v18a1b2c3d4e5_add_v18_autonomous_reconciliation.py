"""Add V18 autonomous reconciliation tables.

Revision ID: v18a1b2c3d4e5
Revises: v17a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v18a1b2c3d4e5"
down_revision = "v17a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drift_signal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(), unique=True, nullable=False),
        sa.Column("drift_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("provider_name", sa.String(), nullable=False, server_default=""),
        sa.Column("expected_value", sa.String(), nullable=False, server_default=""),
        sa.Column("actual_value", sa.String(), nullable=False, server_default=""),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("signal_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("detected_at", sa.String(), nullable=False, server_default=""),
        sa.Column("resolved_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "reconciliation_plan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.String(), unique=True, nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
        sa.Column("drift_signal_ids", sa.String(), nullable=False, server_default=""),
        sa.Column("actions_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("plan_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
        sa.Column("completed_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "reconciliation_step",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("step_id", sa.String(), unique=True, nullable=False),
        sa.Column("execution_id", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=False, server_default=""),
        sa.Column("action_type", sa.String(), nullable=False, server_default=""),
        sa.Column("target_provider", sa.String(), nullable=False, server_default=""),
        sa.Column("outcome", sa.String(), nullable=False, server_default=""),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.String(), nullable=False, server_default=""),
        sa.Column("result_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("executed_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "reconciliation_execution",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("execution_id", sa.String(), unique=True, nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("execution_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("started_at", sa.String(), nullable=False, server_default=""),
        sa.Column("completed_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "convergence_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(), unique=True, nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="unknown"),
        sa.Column("health", sa.String(), nullable=False, server_default="healthy"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("active_drift_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_reconciliation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("issues_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("snapshot_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("timestamp", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("convergence_snapshot")
    op.drop_table("reconciliation_execution")
    op.drop_table("reconciliation_step")
    op.drop_table("reconciliation_plan")
    op.drop_table("drift_signal")
