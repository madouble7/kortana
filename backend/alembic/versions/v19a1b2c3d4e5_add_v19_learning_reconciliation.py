"""Add V19 learning reconciliation tables.

Revision ID: v19a1b2c3d4e5
Revises: v18a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v19a1b2c3d4e5"
down_revision = "v18a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_outcome",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("outcome_id", sa.String(), unique=True, nullable=False),
        sa.Column("execution_id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("drift_type", sa.String(), nullable=False, server_default=""),
        sa.Column("action_types_used", sa.String(), nullable=False, server_default=""),
        sa.Column("verdict", sa.String(), nullable=False, server_default="inconclusive"),
        sa.Column("time_to_resolve_sec", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("retries_needed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("resolution_stable", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("learning_applied", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("outcome_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("recorded_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "action_effectiveness",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("drift_type", sa.String(), nullable=False, server_default=""),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_retries", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_time_to_resolve", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("effectiveness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("computed_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "strategy_recommendation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("recommendation_id", sa.String(), unique=True, nullable=False),
        sa.Column("drift_type", sa.String(), nullable=False),
        sa.Column("recommended_actions", sa.String(), nullable=False, server_default=""),
        sa.Column("recommended_priority", sa.String(), nullable=False, server_default="normal"),
        sa.Column("recommended_max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reasoning", sa.String(), nullable=False, server_default=""),
        sa.Column("based_on_outcomes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommendation_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "adaptive_plan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.String(), unique=True, nullable=False),
        sa.Column("base_plan_id", sa.String(), nullable=False, server_default=""),
        sa.Column("status", sa.String(), nullable=False, server_default="created"),
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
        sa.Column("drift_signal_ids", sa.String(), nullable=False, server_default=""),
        sa.Column("learning_applied", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("overrides_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("recommendation_id", sa.String(), nullable=False, server_default=""),
        sa.Column("plan_hash", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False, server_default=""),
    )
    op.create_table(
        "improvement_metric",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.String(), nullable=False),
        sa.Column("drift_type", sa.String(), nullable=False, server_default=""),
        sa.Column("default_effectiveness_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("learned_effectiveness_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("improvement_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("default_avg_time", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("learned_avg_time", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("time_improvement_pct", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("default_sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("learned_sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metric_hash", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("improvement_metric")
    op.drop_table("adaptive_plan")
    op.drop_table("strategy_recommendation")
    op.drop_table("action_effectiveness")
    op.drop_table("reconciliation_outcome")
