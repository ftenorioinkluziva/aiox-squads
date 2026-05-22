"""SQLAlchemy models for pipeline execution."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class PipelineRunDB(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    workflow_id: Mapped[str] = mapped_column(String(120), default="wf-analise-processual-completa")
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    current_phase_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    steps: Mapped[list["PipelineStepDB"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="PipelineStepDB.sort_order",
    )
    events: Mapped[list["PipelineEventDB"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="PipelineEventDB.id",
    )
    outputs: Mapped[list["PipelineOutputDB"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="PipelineOutputDB.id",
    )


class PipelineStepDB(Base):
    __tablename__ = "pipeline_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    phase_id: Mapped[str] = mapped_column(String(120), index=True)
    phase_name: Mapped[str] = mapped_column(String(240))
    task_id: Mapped[str] = mapped_column(String(160), index=True)
    task_description: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    dependencies: Mapped[list[str]] = mapped_column(JSONB, default=list)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    run: Mapped[PipelineRunDB] = relationship(back_populates="steps")


class PipelineEventDB(Base):
    __tablename__ = "pipeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped[PipelineRunDB] = relationship(back_populates="events")


class PipelineOutputDB(Base):
    __tablename__ = "pipeline_outputs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    content_md: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped[PipelineRunDB] = relationship(back_populates="outputs")
