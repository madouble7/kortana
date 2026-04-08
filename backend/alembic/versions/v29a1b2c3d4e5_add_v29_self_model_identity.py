"""add V29 self-model identity persistence tables

Revision ID: v29a1b2c3d4e5
Revises: v28a1b2c3d4e5
Create Date: 2026-04-08
"""
import sqlalchemy as sa
from alembic import op

revision = "v29a1b2c3d4e5"
down_revision = "v28a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V29A — trait profile snapshots
    op.create_table(
        "trait_profile",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer, index=True, default=0),
        sa.Column("traits_json", sa.Text, default="{}"),
        sa.Column("domain_averages_json", sa.Text, default="{}"),
        sa.Column("dominant_domain", sa.String, default=""),
        sa.Column("strongest_trait", sa.String, default=""),
        sa.Column("weakest_trait", sa.String, default=""),
        sa.Column("total_delta", sa.Float, default=0.0),
        sa.Column("significant_shifts_json", sa.Text, default="[]"),
        sa.Column("is_stable", sa.Boolean, default=True),
        sa.Column("is_transforming", sa.Boolean, default=False),
        sa.Column("captured_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("profile_hash", sa.String, nullable=True),
    )

    # V29B — narrative chapters
    op.create_table(
        "narrative_chapter",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("chapter_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("chapter_number", sa.Integer, index=True, default=1),
        sa.Column("title", sa.String, default=""),
        sa.Column("theme", sa.String, default="genesis"),
        sa.Column("start_cycle", sa.Integer, default=0),
        sa.Column("end_cycle", sa.Integer, nullable=True),
        sa.Column("events_json", sa.Text, default="[]"),
        sa.Column("trait_deltas_json", sa.Text, default="{}"),
        sa.Column("opening_summary", sa.Text, default=""),
        sa.Column("closing_summary", sa.Text, default=""),
        sa.Column("is_open", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("chapter_hash", sa.String, nullable=True),
    )

    # V29C — trait evolution snapshots
    op.create_table(
        "trait_evolution",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer, index=True, default=0),
        sa.Column("crystallized_traits_json", sa.Text, default="[]"),
        sa.Column("drifting_traits_json", sa.Text, default="[]"),
        sa.Column("volatile_traits_json", sa.Text, default="[]"),
        sa.Column("most_changed", sa.String, default=""),
        sa.Column("most_stable", sa.String, default=""),
        sa.Column("overall_stability", sa.Float, default=1.0),
        sa.Column("trajectories_json", sa.Text, default="{}"),
        sa.Column("captured_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("evolution_hash", sa.String, nullable=True),
    )

    # V29D — continuity reports
    op.create_table(
        "continuity_report",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.String, unique=True, index=True, nullable=False),
        sa.Column("cycle_number", sa.Integer, index=True, default=0),
        sa.Column("coherence_score", sa.Float, default=1.0),
        sa.Column("drift_severity", sa.String, default="none"),
        sa.Column("drift_magnitude", sa.Float, default=0.0),
        sa.Column("identity_verified", sa.Boolean, default=True),
        sa.Column("anchor_count", sa.Integer, default=0),
        sa.Column("drifting_traits_json", sa.Text, default="[]"),
        sa.Column("stable_traits_json", sa.Text, default="[]"),
        sa.Column("foundational_anchors_json", sa.Text, default="[]"),
        sa.Column("anchors_json", sa.Text, default="[]"),
        sa.Column("verified_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("report_hash", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("continuity_report")
    op.drop_table("trait_evolution")
    op.drop_table("narrative_chapter")
    op.drop_table("trait_profile")
