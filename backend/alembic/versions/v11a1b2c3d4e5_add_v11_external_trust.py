"""V11 — Auth providers, identity sessions, bindings, rule versions.

Revision ID: v11a1b2c3d4e5
Revises: v10a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v11a1b2c3d4e5"
down_revision = "v10a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "credential_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("operator_id", sa.String(64), nullable=False, index=True),
        sa.Column("provider_type", sa.String(32), nullable=False, index=True),
        sa.Column("credential_id", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("role_hint", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active", index=True),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("verification_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "identity_session",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("operator_id", sa.String(64), nullable=False, index=True),
        sa.Column("provider_type", sa.String(32), nullable=False, index=True),
        sa.Column("credential_id", sa.String(128), nullable=False),
        sa.Column("verification_level", sa.String(16), nullable=False, server_default="basic"),
        sa.Column("status", sa.String(16), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("session_hash", sa.String(64), nullable=False, index=True),
    )

    op.create_table(
        "identity_binding",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("binding_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("operator_id", sa.String(64), nullable=False, index=True),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("bound_at", sa.DateTime(), nullable=False),
        sa.Column("binding_hash", sa.String(64), nullable=False, index=True),
    )

    op.create_table(
        "rule_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("rule_id", sa.String(64), nullable=False, index=True),
        sa.Column("stage", sa.String(16), nullable=False, server_default="draft", index=True),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("author_id", sa.String(64), nullable=False, index=True),
        sa.Column("reviewer_id", sa.String(64), nullable=True),
        sa.Column("changelog", sa.String(512), nullable=False, server_default=""),
        sa.Column("version_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("promoted_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rule_version")
    op.drop_table("identity_binding")
    op.drop_table("identity_session")
    op.drop_table("credential_record")
