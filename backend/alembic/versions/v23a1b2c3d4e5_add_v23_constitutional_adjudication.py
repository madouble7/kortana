"""V23: constitutional adjudication tables.

Revision ID: v23a1b2c3d4e5
Revises: v22a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v23a1b2c3d4e5"
down_revision = "v22a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "constitutional_waiver",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("waiver_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("article_id", sa.String(), nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("policy_area", sa.String(), nullable=False),
        sa.Column("classification_overridden", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("granted_by", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("conditions_json", sa.Text(), server_default="{}"),
        sa.Column("duration_hours", sa.Integer(), server_default="4"),
        sa.Column("status", sa.String(), nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("waiver_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "constitutional_appeal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("appeal_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("original_check_id", sa.String(), nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False),
        sa.Column("appellant", sa.String(), nullable=False),
        sa.Column("grounds", sa.String(), nullable=False),
        sa.Column("argument", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), server_default="[]"),
        sa.Column("status", sa.String(), nullable=False, server_default="filed"),
        sa.Column("decision_json", sa.Text(), nullable=True),
        sa.Column("escalated_sensitivity", sa.String(), server_default="high"),
        sa.Column("filed_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("appeal_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "emergency_declaration",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("declaration_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("declared_by", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("affected_areas_json", sa.Text(), server_default="[]"),
        sa.Column("powers_json", sa.Text(), server_default="[]"),
        sa.Column("duration_hours", sa.Integer(), server_default="4"),
        sa.Column("status", sa.String(), nullable=False, server_default="declared"),
        sa.Column("review_json", sa.Text(), nullable=True),
        sa.Column("declared_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("declaration_hash", sa.String(), nullable=True),
    )

    op.create_table(
        "adjudication_precedent",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("precedent_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("decision_type", sa.String(), nullable=False, index=True),
        sa.Column("reference_id", sa.String(), nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False, index=True),
        sa.Column("decision_summary", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("strength", sa.String(), nullable=False, server_default="persuasive"),
        sa.Column("cited_articles_json", sa.Text(), server_default="[]"),
        sa.Column("tags_json", sa.Text(), server_default="[]"),
        sa.Column("superseded_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("precedent_hash", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("adjudication_precedent")
    op.drop_table("emergency_declaration")
    op.drop_table("constitutional_appeal")
    op.drop_table("constitutional_waiver")
