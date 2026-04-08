"""V8C/D — Add chaos_scenario_record and human_override tables.

Revision ID: v8c1d2e3f4g5
Revises: v8a1b2c3d4e6
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v8c1d2e3f4g5"
down_revision = "v8a1b2c3d4e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chaos_scenario_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("scenario", sa.String(32), nullable=False, index=True),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=True),
        sa.Column("daemon_mode_before", sa.String(32), nullable=True),
        sa.Column("daemon_mode_after", sa.String(32), nullable=True),
        sa.Column("rollback_triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("alerts_fired", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "human_override",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mode", sa.String(32), nullable=False, index=True),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("created_by", sa.String(64), nullable=False, server_default="matt"),
        sa.Column("audit_hash", sa.String(64), nullable=False, index=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.String(64), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("human_override")
    op.drop_table("chaos_scenario_record")
