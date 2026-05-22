"""pipeline tables

Revision ID: 0001_pipeline_tables
Revises:
Create Date: 2026-05-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_pipeline_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_phase_id", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_pipeline_runs_session_id", "pipeline_runs", ["session_id"])
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])

    op.create_table(
        "pipeline_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase_id", sa.String(length=120), nullable=False),
        sa.Column("phase_name", sa.String(length=240), nullable=False),
        sa.Column("task_id", sa.String(length=160), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dependencies", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_pipeline_steps_agent_id", "pipeline_steps", ["agent_id"])
    op.create_index("ix_pipeline_steps_phase_id", "pipeline_steps", ["phase_id"])
    op.create_index("ix_pipeline_steps_run_id", "pipeline_steps", ["run_id"])
    op.create_index("ix_pipeline_steps_status", "pipeline_steps", ["status"])
    op.create_index("ix_pipeline_steps_task_id", "pipeline_steps", ["task_id"])

    op.create_table(
        "pipeline_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pipeline_events_event_type", "pipeline_events", ["event_type"])
    op.create_index("ix_pipeline_events_run_id", "pipeline_events", ["run_id"])

    op.create_table(
        "pipeline_outputs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pipeline_outputs_run_id", "pipeline_outputs", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_pipeline_outputs_run_id", table_name="pipeline_outputs")
    op.drop_table("pipeline_outputs")
    op.drop_index("ix_pipeline_events_run_id", table_name="pipeline_events")
    op.drop_index("ix_pipeline_events_event_type", table_name="pipeline_events")
    op.drop_table("pipeline_events")
    op.drop_index("ix_pipeline_steps_task_id", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_status", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_run_id", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_phase_id", table_name="pipeline_steps")
    op.drop_index("ix_pipeline_steps_agent_id", table_name="pipeline_steps")
    op.drop_table("pipeline_steps")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_session_id", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
