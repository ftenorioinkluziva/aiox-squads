"""chat and document tables

Revision ID: 0002_chat_document_tables
Revises: 0001_pipeline_tables
Create Date: 2026-05-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_chat_document_tables"
down_revision = "0001_pipeline_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("session_id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("phase", sa.String(length=40), nullable=False),
        sa.Column("considerations", sa.Text(), nullable=False),
        sa.Column("context_summary", sa.Text(), nullable=False),
        sa.Column("active_agents", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_sessions_phase", "chat_sessions", ["phase"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("agent_id", sa.String(length=120), nullable=True),
        sa.Column("agent_name", sa.String(length=160), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_chat_messages_role", "chat_messages", ["role"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "documents",
        sa.Column("doc_id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=True),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("total_pages", sa.Integer(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_parties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("process_number", sa.String(length=120), nullable=False),
        sa.Column("court", sa.String(length=120), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("text_page_count", sa.Integer(), nullable=False),
        sa.Column("scanned_page_count", sa.Integer(), nullable=False),
        sa.Column("ocr_required", sa.Boolean(), nullable=False),
        sa.Column("extraction_status", sa.String(length=80), nullable=False),
        sa.Column("extraction_warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_extraction_status", "documents", ["extraction_status"])
    op.create_index("ix_documents_ocr_required", "documents", ["ocr_required"])
    op.create_index("ix_documents_session_id", "documents", ["session_id"])
    op.create_index("ix_documents_sha256", "documents", ["sha256"])

    op.create_table(
        "document_pages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.String(length=36), sa.ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("image_count", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=80), nullable=False),
        sa.Column("extraction_status", sa.String(length=80), nullable=False),
        sa.Column("needs_ocr", sa.Boolean(), nullable=False),
        sa.Column("thumbnail_path", sa.Text(), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("ocr_status", sa.String(length=80), nullable=False),
        sa.Column("ocr_confidence", sa.Integer(), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_document_pages_doc_id", "document_pages", ["doc_id"])
    op.create_index("ix_document_pages_extraction_status", "document_pages", ["extraction_status"])
    op.create_index("ix_document_pages_needs_ocr", "document_pages", ["needs_ocr"])
    op.create_index("ix_document_pages_page_number", "document_pages", ["page_number"])

    op.create_table(
        "document_clips",
        sa.Column("clip_id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=True),
        sa.Column("doc_id", sa.String(length=36), sa.ForeignKey("documents.doc_id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("x0", sa.Float(), nullable=False),
        sa.Column("y0", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
        sa.Column("clip_type", sa.String(length=40), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_clips_doc_id", "document_clips", ["doc_id"])
    op.create_index("ix_document_clips_session_id", "document_clips", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_document_clips_session_id", table_name="document_clips")
    op.drop_index("ix_document_clips_doc_id", table_name="document_clips")
    op.drop_table("document_clips")
    op.drop_index("ix_document_pages_page_number", table_name="document_pages")
    op.drop_index("ix_document_pages_needs_ocr", table_name="document_pages")
    op.drop_index("ix_document_pages_extraction_status", table_name="document_pages")
    op.drop_index("ix_document_pages_doc_id", table_name="document_pages")
    op.drop_table("document_pages")
    op.drop_index("ix_documents_sha256", table_name="documents")
    op.drop_index("ix_documents_session_id", table_name="documents")
    op.drop_index("ix_documents_ocr_required", table_name="documents")
    op.drop_index("ix_documents_extraction_status", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_role", table_name="chat_messages")
    op.drop_index("ix_chat_messages_created_at", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_phase", table_name="chat_sessions")
    op.drop_table("chat_sessions")
