"""add v21 institutional learning controls

Revision ID: v21a1b2c3d4e5
Revises: v20a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v21a1b2c3d4e5"
down_revision = "v20a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V21A — policy proposals
    op.create_table(
        "policy_proposal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proposal_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("source_amendment_id", sa.String(), nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False),
        sa.Column("current_rule", sa.String(), nullable=False),
        sa.Column("proposed_rule", sa.String(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("submitted_at", sa.String(), server_default=""),
        sa.Column("reviewed_at", sa.String(), server_default=""),
        sa.Column("promoted_at", sa.String(), server_default=""),
        sa.Column("reviewer", sa.String(), server_default=""),
        sa.Column("review_notes", sa.Text(), server_default=""),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("proposal_hash", sa.String(), nullable=False),
    )

    # V21B — approval decisions
    op.create_table(
        "approval_decision",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("decision_type", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("conditions", sa.Text(), server_default=""),
        sa.Column("decided_at", sa.String(), nullable=False),
        sa.Column("decision_hash", sa.String(), nullable=False),
    )

    # V21C — rollback points
    op.create_table(
        "rollback_point",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("point_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("prior_state", sa.Text(), nullable=False),
        sa.Column("applied_state", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("rolled_back", sa.Boolean(), server_default="0"),
        sa.Column("rolled_back_at", sa.String(), server_default=""),
        sa.Column("rollback_reason", sa.Text(), server_default=""),
        sa.Column("rollback_hash", sa.String(), nullable=False),
    )

    # V21D — evolution events
    op.create_table(
        "evolution_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("event_type", sa.String(), nullable=False, index=True),
        sa.Column("subject_id", sa.String(), nullable=False, index=True),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.String(), nullable=False),
        sa.Column("event_hash", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evolution_event")
    op.drop_table("rollback_point")
    op.drop_table("approval_decision")
    op.drop_table("policy_proposal")
