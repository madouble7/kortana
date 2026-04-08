"""V26 — heartbeat & continuous self-cycle tables.

Revision ID: v26a1b2c3d4e5
Revises: v25a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v26a1b2c3d4e5"
down_revision = "v25a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "heartbeat",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("beat_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, nullable=False),
        sa.Column("state", sa.String(), nullable=False, server_default="alive"),
        sa.Column("phase", sa.String(), nullable=False, server_default="observe"),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), server_default="0"),
        sa.Column("observations_json", sa.Text(), server_default="[]"),
        sa.Column("decisions_json", sa.Text(), server_default="[]"),
        sa.Column("actions_json", sa.Text(), server_default="[]"),
        sa.Column("deferrals_json", sa.Text(), server_default="[]"),
        sa.Column("reflections_json", sa.Text(), server_default="[]"),
        sa.Column("beat_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "cycle_memory",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cycle_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), server_default="0"),
        sa.Column("observations_json", sa.Text(), server_default="[]"),
        sa.Column("decisions_json", sa.Text(), server_default="[]"),
        sa.Column("actions_json", sa.Text(), server_default="[]"),
        sa.Column("deferrals_json", sa.Text(), server_default="[]"),
        sa.Column("reflections_json", sa.Text(), server_default="[]"),
        sa.Column("context_inherited_json", sa.Text(), server_default="{}"),
        sa.Column("context_bequeathed_json", sa.Text(), server_default="{}"),
        sa.Column("finalized", sa.Integer(), server_default="0"),
        sa.Column("cycle_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "health_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, nullable=False),
        sa.Column("overall_level", sa.String(), nullable=False, server_default="healthy"),
        sa.Column("overall_score", sa.Float(), server_default="0"),
        sa.Column("dimensions_json", sa.Text(), server_default="{}"),
        sa.Column("anomalies_json", sa.Text(), server_default="[]"),
        sa.Column("recommendations_json", sa.Text(), server_default="[]"),
        sa.Column("assessed_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("snapshot_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "degradation_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("record_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("mode", sa.String(), nullable=False, server_default="full_operation"),
        sa.Column("trigger", sa.String(), nullable=False),
        sa.Column("previous_mode", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), server_default=""),
        sa.Column("cycle_number", sa.Integer(), index=True, server_default="0"),
        sa.Column("entered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("exited_at", sa.DateTime(), nullable=True),
        sa.Column("degradation_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("degradation_record")
    op.drop_table("health_snapshot")
    op.drop_table("cycle_memory")
    op.drop_table("heartbeat")
