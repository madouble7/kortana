"""Add canary_runs table for V4 persistent eval

Revision ID: v4a1b2c3d4e5
Revises: g8h9i0j1k2l3
Create Date: 2026-04-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "v4a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "g8h9i0j1k2l3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create canary_runs table for V4 continuous eval."""
    op.create_table(
        "canary_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True, index=True),
        sa.Column("branch", sa.String(length=255), nullable=True, index=True),
        sa.Column("total_cycles", sa.Integer(), nullable=False),
        sa.Column("task_pool_size", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False, index=True),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("score_shift_delta", sa.Float(), nullable=True),
        sa.Column("goal_alignment_delta", sa.Float(), nullable=True),
        sa.Column("outcome_growth", sa.Float(), nullable=True),
        sa.Column("top3_churn_rate", sa.Float(), nullable=True),
        sa.Column("score_spread_delta", sa.Float(), nullable=True),
        sa.Column(
            "promotion_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("promotion_reasons", sa.JSON(), nullable=True),
        sa.Column(
            "triggered_by",
            sa.String(length=64),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("snapshot_summary", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
    )


def downgrade() -> None:
    """Drop canary_runs table."""
    op.drop_table("canary_runs")
