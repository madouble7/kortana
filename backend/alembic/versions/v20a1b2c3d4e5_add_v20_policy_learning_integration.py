"""Add V20 policy-learning integration tables.

Revision ID: v20a1b2c3d4e5
Revises: v19a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v20a1b2c3d4e5"
down_revision = "v19a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trust_calibration",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("calibration_id", sa.String(), unique=True, nullable=False),
        sa.Column("trust_level", sa.String(), nullable=False, server_default="untrusted"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("factors_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("evidence_summary", sa.String(), nullable=False, server_default=""),
        sa.Column("calibration_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("calibrated_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "autonomy_threshold",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("threshold_id", sa.String(), unique=True, nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("auto_threshold", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("ho_threshold", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("approval_threshold", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trust_level_required", sa.String(), nullable=False, server_default="provisional"),
        sa.Column("reason", sa.String(), nullable=False, server_default=""),
        sa.Column("threshold_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("adjusted_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "policy_amendment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("amendment_id", sa.String(), unique=True, nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False, server_default="governance"),
        sa.Column("current_rule", sa.String(), nullable=False, server_default=""),
        sa.Column("proposed_rule", sa.String(), nullable=False, server_default=""),
        sa.Column("justification", sa.String(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("amendment_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
        sa.Column("resolved_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "governance_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", sa.String(), unique=True, nullable=False),
        sa.Column("trust_level", sa.String(), nullable=False, server_default="untrusted"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evolution_stage", sa.String(), nullable=False, server_default="static"),
        sa.Column("autonomy_categories", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_amendments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applied_amendments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amendments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("snapshot_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "governance_evolution",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evolution_id", sa.String(), unique=True, nullable=False),
        sa.Column("evolution_stage", sa.String(), nullable=False, server_default="static"),
        sa.Column("trust_level", sa.String(), nullable=False, server_default="untrusted"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("categories_adjusted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("amendments_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evolution_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("governance_evolution")
    op.drop_table("governance_snapshot")
    op.drop_table("policy_amendment")
    op.drop_table("autonomy_threshold")
    op.drop_table("trust_calibration")
