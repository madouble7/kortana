"""add v22 constitutional governance

Revision ID: v22a1b2c3d4e5
Revises: v21a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v22a1b2c3d4e5"
down_revision = "v21a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V22A — constitutional articles
    op.create_table(
        "constitutional_article",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("sensitivity", sa.String(), nullable=False),
        sa.Column("boundary_rule", sa.Text(), nullable=False),
        sa.Column("violation_severity", sa.String(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("article_hash", sa.String(), nullable=False),
    )

    # V22B — quorum votes
    op.create_table(
        "quorum_vote",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("vote_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("voter", sa.String(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("identity_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("voted_at", sa.String(), nullable=False),
        sa.Column("vote_hash", sa.String(), nullable=False),
    )

    # V22C — boundary checks
    op.create_table(
        "boundary_check",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("check_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("violations_json", sa.Text(), nullable=False),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("articles_checked", sa.Integer(), nullable=False),
        sa.Column("policy_area", sa.String(), nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("sensitivity", sa.String(), nullable=False),
        sa.Column("checked_at", sa.String(), nullable=False),
        sa.Column("check_hash", sa.String(), nullable=False),
    )

    # V22D — constitutional compliance
    op.create_table(
        "constitutional_compliance",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proof_id", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("proposal_id", sa.String(), nullable=False, index=True),
        sa.Column("all_checks_passed", sa.Boolean(), nullable=False),
        sa.Column("checks_performed", sa.Integer(), nullable=False),
        sa.Column("violations_found", sa.Integer(), nullable=False),
        sa.Column("warnings_found", sa.Integer(), nullable=False),
        sa.Column("boundary_checks_json", sa.Text(), nullable=False),
        sa.Column("issued_at", sa.String(), nullable=False),
        sa.Column("proof_hash", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("constitutional_compliance")
    op.drop_table("boundary_check")
    op.drop_table("quorum_vote")
    op.drop_table("constitutional_article")
