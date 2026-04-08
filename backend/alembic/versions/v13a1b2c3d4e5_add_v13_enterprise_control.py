"""V13 — Enterprise control integration tables.

Revision ID: v13a1b2c3d4e5
Revises: v12a1b2c3d4e5
"""
from alembic import op
import sqlalchemy as sa

revision = "v13a1b2c3d4e5"
down_revision = "v12a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idp_sync",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("discovery_url", sa.String(256), nullable=False),
        sa.Column("issuer_url", sa.String(256), nullable=True),
        sa.Column("sync_state", sa.String(32), default="pending"),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("config_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "secret_reference",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("secret_id", sa.String(64), nullable=False),
        sa.Column("backend", sa.String(32), default="local"),
        sa.Column("path", sa.String(256), nullable=True),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("ref_hash", sa.String(64), nullable=True),
    )
    op.create_table(
        "attestation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("attestation_id", sa.String(64), nullable=False),
        sa.Column("attestation_type", sa.String(32), nullable=False),
        sa.Column("subject", sa.String(128), nullable=True),
        sa.Column("signature", sa.String(256), nullable=True),
        sa.Column("signer_id", sa.String(64), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "trust_signal",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("signal_id", sa.String(64), nullable=False),
        sa.Column("signal_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float(), default=0.0),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("signal_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "trust_evaluation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evaluation_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=True),
        sa.Column("passed", sa.Boolean(), default=False),
        sa.Column("score", sa.Float(), default=0.0),
        sa.Column("missing_signals", sa.Text(), nullable=True),
        sa.Column("eval_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("trust_evaluation")
    op.drop_table("trust_signal")
    op.drop_table("attestation")
    op.drop_table("secret_reference")
    op.drop_table("idp_sync")
