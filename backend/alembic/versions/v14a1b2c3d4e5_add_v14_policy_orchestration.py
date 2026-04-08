"""V14 — Policy orchestration tables.

Revision ID: v14a1b2c3d4e5
Revises: v13a1b2c3d4e5
"""
from alembic import op
import sqlalchemy as sa

revision = "v14a1b2c3d4e5"
down_revision = "v13a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metadata_drift",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("provider_url", sa.String(256), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(32), default="low"),
        sa.Column("detected_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "secret_rotation_schedule",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("secret_id", sa.String(64), nullable=False),
        sa.Column("backend", sa.String(32), default="local"),
        sa.Column("interval_hours", sa.Integer(), default=24),
        sa.Column("next_rotation_at", sa.DateTime(), nullable=True),
        sa.Column("last_rotated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "signer_certificate",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("signer_id", sa.String(64), nullable=False),
        sa.Column("certificate_hash", sa.String(64), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("issuer_name", sa.String(128), nullable=True),
        sa.Column("signer_status", sa.String(32), default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "trust_artifact",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.String(64), nullable=False),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("issuer", sa.String(128), nullable=True),
        sa.Column("subject", sa.String(128), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("artifact_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "artifact_policy",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("policy_name", sa.String(128), nullable=True),
        sa.Column("required_artifacts", sa.Text(), nullable=True),
        sa.Column("require_all", sa.Boolean(), default=True),
        sa.Column("min_artifact_age_hours", sa.Float(), default=0.0),
        sa.Column("max_artifact_age_hours", sa.Float(), default=720.0),
        sa.Column("policy_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("artifact_policy")
    op.drop_table("trust_artifact")
    op.drop_table("signer_certificate")
    op.drop_table("secret_rotation_schedule")
    op.drop_table("metadata_drift")
