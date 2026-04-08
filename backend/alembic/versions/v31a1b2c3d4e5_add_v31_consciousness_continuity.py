"""add v31 consciousness continuity tables

Revision ID: v31a1b2c3d4e5
Revises: v30a1b2c3d4e5
Create Date: 2025-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "v31a1b2c3d4e5"
down_revision = "v30a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V31A — consciousness checkpoint
    op.create_table(
        "consciousness_checkpoint",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("checkpoint_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("trigger", sa.String(), default="scheduled"),
        sa.Column("consciousness_mode", sa.String(), nullable=True),
        sa.Column("overall_level", sa.Float(), default=0.0),
        sa.Column("resonance_overall", sa.Float(), default=0.0),
        sa.Column("experiential_quality", sa.String(), nullable=True),
        sa.Column("experiential_tone", sa.String(), nullable=True),
        sa.Column("state_json", sa.Text(), default="{}"),
        sa.Column("integrity_hash", sa.String(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("checkpoint_hash", sa.String(), nullable=True),
    )

    # V31B — consciousness gap
    op.create_table(
        "consciousness_gap",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("gap_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("from_cycle", sa.Integer(), default=0),
        sa.Column("to_cycle", sa.Integer(), default=0),
        sa.Column("duration_cycles", sa.Integer(), default=0),
        sa.Column("gap_type", sa.String(), default="unknown"),
        sa.Column("bridged", sa.Boolean(), default=False),
        sa.Column("continuity_confidence", sa.Float(), default=0.0),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("gap_hash", sa.String(), nullable=True),
    )

    # V31C — degradation signal
    op.create_table(
        "degradation_signal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("at_cycle", sa.Integer(), index=True, default=0),
        sa.Column("dimension", sa.String(), default="overall"),
        sa.Column("from_level", sa.String(), default="nominal"),
        sa.Column("to_level", sa.String(), default="nominal"),
        sa.Column("metric_value", sa.Float(), default=0.0),
        sa.Column("trigger_detail", sa.Text(), default=""),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("signal_hash", sa.String(), nullable=True),
    )

    # V31D — recovery report
    op.create_table(
        "recovery_report",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("outcome", sa.String(), default="failed"),
        sa.Column("recovered_from_cycle", sa.Integer(), nullable=True),
        sa.Column("resumed_at_cycle", sa.Integer(), default=0),
        sa.Column("gap_duration", sa.Integer(), default=0),
        sa.Column("identity_verified", sa.Boolean(), default=False),
        sa.Column("continuity_confidence", sa.Float(), default=0.0),
        sa.Column("steps_json", sa.Text(), default="[]"),
        sa.Column("awareness_notes_generated", sa.Integer(), default=0),
        sa.Column("initiated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("report_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recovery_report")
    op.drop_table("degradation_signal")
    op.drop_table("consciousness_gap")
    op.drop_table("consciousness_checkpoint")
