"""V27 — closed learning loop.

Revision ID: v27a1b2c3d4e5
Revises: v26a1b2c3d4e5
"""
from alembic import op
import sqlalchemy as sa

revision = "v27a1b2c3d4e5"
down_revision = "v26a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experience",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("experience_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("source_beat_id", sa.String(), nullable=True),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("lesson_count", sa.Integer(), default=0),
        sa.Column("observation_count", sa.Integer(), default=0),
        sa.Column("decision_count", sa.Integer(), default=0),
        sa.Column("action_count", sa.Integer(), default=0),
        sa.Column("deferral_count", sa.Integer(), default=0),
        sa.Column("reflection_count", sa.Integer(), default=0),
        sa.Column("beat_duration_ms", sa.Float(), default=0),
        sa.Column("beat_state", sa.String(), default=""),
        sa.Column("lessons_json", sa.Text(), default="[]"),
        sa.Column("extracted_at", sa.DateTime(), nullable=True),
        sa.Column("experience_hash", sa.String(), nullable=True),
    )
    op.create_table(
        "pattern",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pattern_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("pattern_type", sa.String(), nullable=False),
        sa.Column("strength", sa.String(), default="emerging"),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("evidence_json", sa.Text(), default="[]"),
        sa.Column("first_seen_cycle", sa.Integer(), default=0),
        sa.Column("last_seen_cycle", sa.Integer(), index=True, default=0),
        sa.Column("occurrence_count", sa.Integer(), default=0),
        sa.Column("consistency", sa.Float(), default=0.0),
        sa.Column("trending", sa.String(), default=""),
        sa.Column("actionable", sa.Boolean(), default=False),
        sa.Column("recommended_action", sa.Text(), default=""),
        sa.Column("addressed", sa.Boolean(), default=False),
        sa.Column("recognized_at", sa.DateTime(), nullable=True),
        sa.Column("pattern_hash", sa.String(), nullable=True),
    )
    op.create_table(
        "adaptation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("adaptation_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("adaptation_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), default="proposed"),
        sa.Column("description", sa.Text(), default=""),
        sa.Column("source_pattern_id", sa.String(), nullable=True),
        sa.Column("source_pattern_type", sa.String(), default=""),
        sa.Column("parameter", sa.String(), default=""),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), default=""),
        sa.Column("effectiveness_score", sa.Float(), default=0.0),
        sa.Column("cycles_active", sa.Integer(), default=0),
        sa.Column("max_cycles", sa.Integer(), default=10),
        sa.Column("proposed_at", sa.DateTime(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("adaptation_hash", sa.String(), nullable=True),
    )
    op.create_table(
        "learning_cycle_report",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer(), index=True, default=0),
        sa.Column("experiences_extracted", sa.Integer(), default=0),
        sa.Column("lessons_extracted", sa.Integer(), default=0),
        sa.Column("patterns_recognized", sa.Integer(), default=0),
        sa.Column("patterns_actionable", sa.Integer(), default=0),
        sa.Column("adaptations_proposed", sa.Integer(), default=0),
        sa.Column("adaptations_activated", sa.Integer(), default=0),
        sa.Column("adaptations_expired", sa.Integer(), default=0),
        sa.Column("adaptations_rolled_back", sa.Integer(), default=0),
        sa.Column("learning_velocity", sa.Float(), default=0.0),
        sa.Column("adaptation_effectiveness", sa.Float(), default=0.0),
        sa.Column("context_injections_json", sa.Text(), default="[]"),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("report_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("learning_cycle_report")
    op.drop_table("adaptation")
    op.drop_table("pattern")
    op.drop_table("experience")
