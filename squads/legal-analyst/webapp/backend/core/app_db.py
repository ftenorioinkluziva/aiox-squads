"""SQLAlchemy models for persisted chat sessions and documents."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ChatSessionDB(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(240), default="Nova Analise")
    phase: Mapped[str] = mapped_column(String(40), default="intake", index=True)
    considerations: Mapped[str] = mapped_column(Text, default="")
    context_summary: Mapped[str] = mapped_column(Text, default="")
    active_agents: Mapped[list[str]] = mapped_column(JSONB, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["ChatMessageDB"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageDB.created_at",
    )
    documents: Mapped[list["DocumentDB"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DocumentDB.created_at",
    )
    clips: Mapped[list["DocumentClipDB"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DocumentClipDB.created_at",
    )


class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    attachments: Mapped[list[str]] = mapped_column(JSONB, default=list)
    references: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    session: Mapped[ChatSessionDB] = relationship(back_populates="messages")


class DocumentDB(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500))
    title: Mapped[str] = mapped_column(String(500), default="")
    stored_path: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(120), default="application/pdf")
    sha256: Mapped[str] = mapped_column(String(64), index=True, default="")
    total_pages: Mapped[int] = mapped_column(Integer, default=0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    extracted_parties: Mapped[list[str]] = mapped_column(JSONB, default=list)
    process_number: Mapped[str] = mapped_column(String(120), default="")
    court: Mapped[str] = mapped_column(String(120), default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    text_page_count: Mapped[int] = mapped_column(Integer, default=0)
    scanned_page_count: Mapped[int] = mapped_column(Integer, default=0)
    ocr_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    extraction_status: Mapped[str] = mapped_column(String(80), default="extracted", index=True)
    extraction_warnings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    session: Mapped[ChatSessionDB | None] = relationship(back_populates="documents")
    pages: Mapped[list["DocumentPageDB"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPageDB.page_number",
    )
    clips: Mapped[list["DocumentClipDB"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentPageDB(Base):
    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.doc_id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    images: Mapped[list[str]] = mapped_column(JSONB, default=list)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    text_length: Mapped[int] = mapped_column(Integer, default=0)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    extraction_method: Mapped[str] = mapped_column(String(80), default="text")
    extraction_status: Mapped[str] = mapped_column(String(80), default="extracted", index=True)
    needs_ocr: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_status: Mapped[str] = mapped_column(String(80), default="not_required")
    ocr_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    document: Mapped[DocumentDB] = relationship(back_populates="pages")


class DocumentClipDB(Base):
    __tablename__ = "document_clips"

    clip_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    doc_id: Mapped[str] = mapped_column(ForeignKey("documents.doc_id", ondelete="CASCADE"), index=True)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    x0: Mapped[float] = mapped_column(default=0)
    y0: Mapped[float] = mapped_column(default=0)
    x1: Mapped[float] = mapped_column(default=0)
    y1: Mapped[float] = mapped_column(default=0)
    clip_type: Mapped[str] = mapped_column(String(40), default="excerpt")
    content_text: Mapped[str] = mapped_column(Text, default="")
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str] = mapped_column(String(500), default="")
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped[ChatSessionDB | None] = relationship(back_populates="clips")
    document: Mapped[DocumentDB] = relationship(back_populates="clips")
