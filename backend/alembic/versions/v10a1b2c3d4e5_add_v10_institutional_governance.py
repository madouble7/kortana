"""V10 — Operator identity, governance actions, deploy gate, policy rules.

Revision ID: v10a1b2c3d4e5
Revises: v9a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v10a1b2c3d4e5"
down_revision = "v9a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operator_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("operator_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, index=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("identity_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "governance_action",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("operator_id", sa.String(64), nullable=False, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("action", sa.String(64), nullable=False, index=True),
        sa.Column("resource", sa.String(128), nullable=False, index=True),
        sa.Column("identity_hash", sa.String(64), nullable=False),
        sa.Column("action_signature", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "deploy_gate_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("operator_id", sa.String(64), nullable=False, index=True),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=True),
        sa.Column("blocking_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warnings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gate_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "policy_rule",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(256), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )

    op.create_table(
        "policy_evaluation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action", sa.String(32), nullable=False, index=True),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("matched_rule_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_rule_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("facts_snapshot", sa.JSON(), nullable=True),
        sa.Column("decision_hash", sa.String(64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("policy_evaluation")
    op.drop_table("policy_rule")
    op.drop_table("deploy_gate_record")
    op.drop_table("governance_action")
    op.drop_table("operator_record")
