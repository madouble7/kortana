"""V17 — closed-loop real-world enforcement.

Revision ID: v17a1b2c3d4e5
Revises: v16a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v17a1b2c3d4e5"
down_revision = "v16a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V17A — provider client records
    op.create_table(
        "provider_client",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_name", sa.String(128), nullable=False),
        sa.Column("provider_type", sa.String(32), server_default="kubernetes"),
        sa.Column("endpoint", sa.String(512), server_default=""),
        sa.Column("namespace", sa.String(64), server_default="default"),
        sa.Column("connection_state", sa.String(32), server_default="disconnected"),
        sa.Column("current_version", sa.String(64), server_default=""),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
    )

    # V17B — rollout action records
    op.create_table(
        "rollout_action",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action_id", sa.String(64), nullable=False),
        sa.Column("provider_name", sa.String(128), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("strategy", sa.String(32), server_default="rolling"),
        sa.Column("status", sa.String(32), server_default="planned"),
        sa.Column("step_count", sa.Integer(), server_default="0"),
        sa.Column("auto_rollback", sa.Boolean(), server_default="1"),
        sa.Column("action_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # V17C — feedback trigger records
    op.create_table(
        "feedback_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trigger_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("condition", sa.String(32), nullable=False),
        sa.Column("threshold", sa.Float(), server_default="5.0"),
        sa.Column("action", sa.String(32), server_default="alert"),
        sa.Column("pipeline_scope", sa.String(64), server_default=""),
        sa.Column("provider_scope", sa.String(64), server_default=""),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("trigger_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # V17C — feedback evaluation records
    op.create_table(
        "feedback_evaluation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evaluation_id", sa.String(64), nullable=False),
        sa.Column("signal_id", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(32), server_default="clean"),
        sa.Column("trigger_count", sa.Integer(), server_default="0"),
        sa.Column("has_rollback", sa.Boolean(), server_default="0"),
        sa.Column("has_escalation", sa.Boolean(), server_default="0"),
        sa.Column("evaluation_hash", sa.String(64), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=True),
    )

    # V17D — evidence entry records
    op.create_table(
        "evidence_entry",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entry_id", sa.String(64), nullable=False),
        sa.Column("chain_id", sa.String(64), nullable=False),
        sa.Column("sequence", sa.Integer(), server_default="0"),
        sa.Column("evidence_type", sa.String(32), server_default="decision"),
        sa.Column("actor", sa.String(128), server_default=""),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("previous_hash", sa.String(64), server_default=""),
        sa.Column("entry_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("evidence_entry")
    op.drop_table("feedback_evaluation")
    op.drop_table("feedback_trigger")
    op.drop_table("rollout_action")
    op.drop_table("provider_client")
