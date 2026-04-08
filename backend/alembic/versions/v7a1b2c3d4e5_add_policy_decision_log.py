"""V7: add policy_decision_log table for audit trail.

Revision ID: v7a1b2c3d4e5
Revises: v4merge000001
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "v7a1b2c3d4e5"
down_revision = "v4merge000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_decision_log",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("decision_type", sa.String(32), nullable=False, index=True),
        sa.Column("actor", sa.String(32), nullable=False, server_default="daemon"),
        sa.Column("action", sa.String(32), nullable=False, index=True),
        sa.Column("from_state", sa.String(64), nullable=True),
        sa.Column("to_state", sa.String(64), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("audit_hash", sa.String(64), nullable=False, index=True),
        sa.Column("commit_sha", sa.String(64), nullable=True, index=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("policy_decision_log")
