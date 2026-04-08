"""V24: constitutional procedure tables.

Revision ID: v24a1b2c3d4e5
Revises: v23a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v24a1b2c3d4e5"
down_revision = "v23a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V24A: standing checks
    op.create_table(
        "standing_check",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("actor", sa.String, nullable=False, index=True),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("policy_area", sa.String, nullable=True),
        sa.Column("allowed", sa.Boolean, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("checked_at", sa.DateTime, server_default=sa.func.now()),
    )

    # V24B: procedural deadlines
    op.create_table(
        "procedural_deadline",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("deadline_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("reference_id", sa.String, nullable=False, index=True),
        sa.Column("deadline_type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("due_at", sa.DateTime, nullable=False),
        sa.Column("original_due_at", sa.DateTime, nullable=False),
        sa.Column("met_at", sa.DateTime, nullable=True),
        sa.Column("extensions", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("deadline_hash", sa.String, nullable=True),
    )

    # V24C: recusal records
    op.create_table(
        "recusal_record",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("recusal_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("actor", sa.String, nullable=False, index=True),
        sa.Column("reference_id", sa.String, nullable=False, index=True),
        sa.Column("conflict_type", sa.String, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("mandatory", sa.Boolean, server_default="0"),
        sa.Column("recused_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("recusal_hash", sa.String, nullable=True),
    )

    # V24D: published reasoning
    op.create_table(
        "published_reasoning",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("reasoning_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("reference_id", sa.String, nullable=False, index=True),
        sa.Column("decision_type", sa.String, nullable=False, index=True),
        sa.Column("sections_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("cited_articles_json", sa.Text, server_default="[]"),
        sa.Column("cited_precedents_json", sa.Text, server_default="[]"),
        sa.Column("author", sa.String, nullable=True),
        sa.Column("published_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("reasoning_hash", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("published_reasoning")
    op.drop_table("recusal_record")
    op.drop_table("procedural_deadline")
    op.drop_table("standing_check")
