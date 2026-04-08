"""V8 — Add rollback_event and policy_version tables.

Revision ID: v8a1b2c3d4e6
Revises: v7a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v8a1b2c3d4e6"
down_revision = "v7a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rollback_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("trigger", sa.String(32), nullable=False, index=True),
        sa.Column("from_mode", sa.String(32), nullable=False),
        sa.Column("to_mode", sa.String(32), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("original_decision_hash", sa.String(64), nullable=True, index=True),
        sa.Column("policy_version", sa.Integer(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "policy_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version", sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("max_changes_per_window", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("window_seconds", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("min_consecutive_promoted", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("max_mode", sa.String(32), nullable=False, server_default="auto"),
        sa.Column("auto_rollback_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_by", sa.String(32), nullable=False, server_default="daemon"),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("policy_version")
    op.drop_table("rollback_event")
