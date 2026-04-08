"""V15 — Execution-backed orchestration.

Revision ID: v15a1b2c3d4e5
Revises: v14a1b2c3d4e5
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "v15a1b2c3d4e5"
down_revision = "v14a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V15A — fetch execution
    op.create_table(
        "fetch_execution",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("fetch_id", sa.String(64), nullable=False),
        sa.Column("provider_url", sa.String(256), nullable=False),
        sa.Column("status", sa.String(32), server_default="success"),
        sa.Column("attempt_count", sa.Integer, server_default="1"),
        sa.Column("response_time_ms", sa.Float, server_default="0.0"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("fetched_at", sa.DateTime, nullable=True),
    )

    # V15B — client operation
    op.create_table(
        "client_operation",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("operation_id", sa.String(64), nullable=False),
        sa.Column("backend_name", sa.String(64), nullable=False),
        sa.Column("operation_type", sa.String(32), server_default="read"),
        sa.Column("secret_id", sa.String(64), nullable=True),
        sa.Column("success", sa.Boolean, server_default="1"),
        sa.Column("latency_ms", sa.Float, server_default="0.0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("operation_hash", sa.String(64), nullable=True),
        sa.Column("executed_at", sa.DateTime, nullable=True),
    )

    # V15C — CA source
    op.create_table(
        "ca_source",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ca_id", sa.String(64), nullable=False),
        sa.Column("ca_name", sa.String(128), nullable=True),
        sa.Column("ca_type", sa.String(32), server_default="public_ca"),
        sa.Column("crl_endpoint", sa.String(256), nullable=True),
        sa.Column("ocsp_endpoint", sa.String(256), nullable=True),
        sa.Column("root_cert_hash", sa.String(64), nullable=True),
        sa.Column("sync_interval_seconds", sa.Integer, server_default="3600"),
        sa.Column("enabled", sa.Boolean, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    # V15D — pipeline gate
    op.create_table(
        "pipeline_gate",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("gate_id", sa.String(64), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("required_artifact_types", sa.Text, nullable=True),
        sa.Column("require_signer_validation", sa.Boolean, server_default="0"),
        sa.Column("require_secret_health", sa.Boolean, server_default="0"),
        sa.Column("max_allowed_vulnerabilities", sa.Integer, server_default="0"),
        sa.Column("auto_rollback_on_failure", sa.Boolean, server_default="1"),
        sa.Column("enabled", sa.Boolean, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )

    # V15D — deployment pipeline
    op.create_table(
        "deployment_pipeline",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pipeline_id", sa.String(64), nullable=False),
        sa.Column("version_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("current_stage", sa.String(32), server_default="build"),
        sa.Column("pipeline_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("deployment_pipeline")
    op.drop_table("pipeline_gate")
    op.drop_table("ca_source")
    op.drop_table("client_operation")
    op.drop_table("fetch_execution")
