"""add V28 intrinsic goal engine tables

Revision ID: v28a1b2c3d4e5
Revises: v27a1b2c3d4e5
Create Date: 2026-04-08 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "v28a1b2c3d4e5"
down_revision = "v27a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "desire",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("desire_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("intensity", sa.Float(), server_default="0.0"),
        sa.Column("persistence", sa.Integer(), server_default="1"),
        sa.Column("source_dimension", sa.String(), nullable=True),
        sa.Column("source_evidence", sa.String(), nullable=True),
        sa.Column("first_felt_cycle", sa.Integer(), server_default="0"),
        sa.Column("last_reinforced_cycle", sa.Integer(), server_default="0"),
        sa.Column("peak_intensity", sa.Float(), server_default="0.0"),
        sa.Column("crystallized", sa.Boolean(), server_default="false"),
        sa.Column("crystallized_goal_id", sa.String(), nullable=True),
        sa.Column("formed_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("desire_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "goal_blueprint",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blueprint_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("source_desire_id", sa.String(), nullable=False),
        sa.Column("source_desire_description", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
        sa.Column("suggested_priority", sa.Float(), server_default="0.0"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("success_criteria", sa.String(), nullable=True),
        sa.Column("accepted", sa.Boolean(), server_default="false"),
        sa.Column("accepted_goal_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("blueprint_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "pursuit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pursuit_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("goal_id", sa.String(), nullable=False),
        sa.Column("source_desire_id", sa.String(), nullable=True),
        sa.Column("source_blueprint_id", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("goal_title", sa.String(), nullable=True),
        sa.Column("started_cycle", sa.Integer(), server_default="0"),
        sa.Column("current_progress", sa.Float(), server_default="0.0"),
        sa.Column("stall_count", sa.Integer(), server_default="0"),
        sa.Column("escalated", sa.Boolean(), server_default="false"),
        sa.Column("redirected", sa.Boolean(), server_default="false"),
        sa.Column("redirect_reason", sa.String(), nullable=True),
        sa.Column("checkpoints_json", sa.Text(), server_default="[]"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "motivation_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False),
        sa.Column("dimensions_json", sa.Text(), server_default="[]"),
        sa.Column("dominant_dimension", sa.String(), nullable=True),
        sa.Column("overall_drive", sa.Float(), server_default="0.0"),
        sa.Column("desire_count", sa.Integer(), server_default="0"),
        sa.Column("active_pursuits", sa.Integer(), server_default="0"),
        sa.Column("stalled_pursuits", sa.Integer(), server_default="0"),
        sa.Column("satisfaction_rate", sa.Float(), server_default="0.0"),
        sa.Column("is_driven", sa.Boolean(), server_default="false"),
        sa.Column("is_drifting", sa.Boolean(), server_default="false"),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("snapshot_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("motivation_snapshot")
    op.drop_table("pursuit")
    op.drop_table("goal_blueprint")
    op.drop_table("desire")
