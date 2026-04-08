"""add v30 unified consciousness layer

Revision ID: v30a1b2c3d4e5
Revises: v29a1b2c3d4e5
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "v30a1b2c3d4e5"
down_revision = "v29a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V30A: consciousness_state
    op.create_table(
        "consciousness_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("state_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("vitality", sa.Float(), default=0.5),
        sa.Column("learning_depth", sa.Float(), default=0.3),
        sa.Column("intentionality", sa.Float(), default=0.3),
        sa.Column("self_coherence", sa.Float(), default=0.3),
        sa.Column("integration", sa.Float(), default=0.5),
        sa.Column("mode", sa.String(), default="dormant"),
        sa.Column("dominant_dimension", sa.String(), nullable=True),
        sa.Column("overall_level", sa.Float(), default=0.5),
        sa.Column("subsystem_digest_json", sa.Text(), default="{}"),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("state_hash", sa.String(), nullable=True),
    )

    # V30B: experiential_moment
    op.create_table(
        "experiential_moment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("moment_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("quality", sa.String(), default="muted"),
        sa.Column("tone", sa.String(), default="dull"),
        sa.Column("salience", sa.String(), default="balanced"),
        sa.Column("consciousness_mode", sa.String(), default="dormant"),
        sa.Column("tensions_json", sa.Text(), default="[]"),
        sa.Column("overall_level", sa.Float(), default=0.5),
        sa.Column("tension_count", sa.Integer(), default=0),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("moment_hash", sa.String(), nullable=True),
    )

    # V30C: resonance_snapshot
    op.create_table(
        "resonance_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("overall_resonance", sa.Float(), default=0.5),
        sa.Column("strongest_pair", sa.String(), nullable=True),
        sa.Column("weakest_pair", sa.String(), nullable=True),
        sa.Column("hotspot_count", sa.Integer(), default=0),
        sa.Column("harmony_count", sa.Integer(), default=0),
        sa.Column("pairs_json", sa.Text(), default="[]"),
        sa.Column("is_harmonious", sa.Boolean(), default=True),
        sa.Column("is_conflicted", sa.Boolean(), default=False),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("snapshot_hash", sa.String(), nullable=True),
    )

    # V30D: awareness_note
    op.create_table(
        "awareness_note",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("note_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("trigger", sa.String(), default="milestone"),
        sa.Column("observation", sa.Text(), default=""),
        sa.Column("significance", sa.String(), default="minor"),
        sa.Column("context_json", sa.Text(), default="{}"),
        sa.Column("captured_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("note_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("awareness_note")
    op.drop_table("resonance_snapshot")
    op.drop_table("experiential_moment")
    op.drop_table("consciousness_state")
