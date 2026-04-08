"""V12 — Production federation tables.

Revision ID: v12a1b2c3d4e5
Revises: v11a1b2c3d4e5
"""
from alembic import op
import sqlalchemy as sa

revision = "v12a1b2c3d4e5"
down_revision = "v11a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oidc_provider",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("issuer_url", sa.String(256), nullable=False),
        sa.Column("client_id", sa.String(128), nullable=False),
        sa.Column("audience", sa.String(128), nullable=True),
        sa.Column("supported_algorithms", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), default=True),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
    )
    op.create_table(
        "key_rotation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key_id", sa.String(64), nullable=False),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("operator_id", sa.String(64), nullable=False),
        sa.Column("rotation_interval_hours", sa.Integer(), default=720),
        sa.Column("grace_period_hours", sa.Integer(), default=24),
        sa.Column("state", sa.String(32), default="active"),
        sa.Column("next_rotation_at", sa.DateTime(), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(), nullable=True),
        sa.Column("schedule_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "rotation_event",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("key_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("old_credential_id", sa.String(64), nullable=True),
        sa.Column("new_credential_id", sa.String(64), nullable=True),
        sa.Column("initiated_by", sa.String(64), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "ci_credential_check",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("checkpoint", sa.String(32), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("operator_id", sa.String(64), nullable=True),
        sa.Column("passed", sa.Boolean(), default=False),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column("policy_applied", sa.String(64), nullable=True),
        sa.Column("check_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "authenticated_promotion",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("operator_id", sa.String(64), nullable=True),
        sa.Column("session_verification_level", sa.String(32), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("authenticated_promotion")
    op.drop_table("ci_credential_check")
    op.drop_table("rotation_event")
    op.drop_table("key_rotation")
    op.drop_table("oidc_provider")
