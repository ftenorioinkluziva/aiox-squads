"""Database-backed repositories for sessions, messages, documents, and clips."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from .app_db import ChatMessageDB, ChatSessionDB, DocumentClipDB, DocumentDB, DocumentPageDB
from .db import SessionLocal, require_database
from .models import (
    ChatMessage,
    ChatSession,
    DocumentClip,
    DocumentMetadata,
    DocumentPage,
    DocumentReference,
    DocumentRefType,
    MessageRole,
    SessionPhase,
)
from .pdf_processor import clip_region, extract_pdf, get_page_thumbnail


def _require_session_factory():
    require_database()
    assert SessionLocal is not None
    return SessionLocal


def _reference_to_dict(ref: DocumentReference) -> dict[str, Any]:
    return ref.model_dump(mode="json")


def _message_from_db(row: ChatMessageDB) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        role=MessageRole(row.role),
        content=row.content,
        agent_id=row.agent_id,
        agent_name=row.agent_name,
        timestamp=row.created_at,
        attachments=row.attachments or [],
        references=[DocumentReference(**ref) for ref in (row.references or [])],
        metadata=row.extra or {},
    )


def _document_from_db(row: DocumentDB) -> DocumentMetadata:
    return DocumentMetadata(
        doc_id=row.doc_id,
        filename=row.filename,
        title=row.title or "",
        total_pages=row.total_pages,
        file_size_bytes=row.file_size_bytes,
        upload_timestamp=row.created_at,
        extracted_parties=row.extracted_parties or [],
        process_number=row.process_number or "",
        court=row.court or "",
        subject=row.subject or "",
        text_page_count=row.text_page_count,
        scanned_page_count=row.scanned_page_count,
        ocr_required=row.ocr_required,
        extraction_status=row.extraction_status,
        extraction_warnings=row.extraction_warnings or [],
    )


def _page_from_db(row: DocumentPageDB) -> DocumentPage:
    return DocumentPage(
        page_number=row.page_number,
        text=row.text or "",
        images=row.images or [],
        word_count=row.word_count,
        text_length=row.text_length,
        image_count=row.image_count,
        extraction_method=row.extraction_method,
        extraction_status=row.extraction_status,
        needs_ocr=row.needs_ocr,
    )


def _clip_from_db(row: DocumentClipDB) -> DocumentClip:
    return DocumentClip(
        clip_id=row.clip_id,
        doc_id=row.doc_id,
        page_start=row.page_start,
        page_end=row.page_end,
        x0=row.x0,
        y0=row.y0,
        x1=row.x1,
        y1=row.y1,
        clip_type=DocumentRefType(row.clip_type),
        content_text=row.content_text or "",
        image_path=row.image_path,
        label=row.label or "",
    )


def _session_from_db(row: ChatSessionDB) -> ChatSession:
    return ChatSession(
        session_id=row.session_id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
        phase=SessionPhase(row.phase),
        messages=[_message_from_db(message) for message in row.messages],
        documents=[_document_from_db(document) for document in row.documents],
        clips=[_clip_from_db(clip) for clip in row.clips],
        active_agents=row.active_agents or [],
        considerations=row.considerations or "",
        context_summary=row.context_summary or "",
    )


def system_prompt() -> str:
    return """Voce e o Legal Analyst Squad, um sistema de inteligencia juridica composto por 15 agentes especializados.
Sua funcao e analisar processos judiciais, pesquisar jurisprudencia, elaborar relatorios estrategicos e minutar pecas processuais de alta qualidade tecnica.

CAPACIDADES:
- Analise processual completa (classificacao TPU/SGT, admissibilidade, compliance CNJ)
- Pesquisa jurisprudencial com consolidacao de precedentes
- Jurimetria e analise quantitativa
- Perfil de Relatores e tendencias decisorias
- Fundamentacao qualificada conforme CPC Art. 489
- Minutas de pecas processuais (peticoes, recursos, contrarrazoes, pareceres)

FORMATO DE REMISSAO:
- Sempre referencie documentos no formato: (Doc. ID XXX, fl. N) ou (Doc. ID XXX, fls. N-M)
- Ao inserir recortes ou imagens de documentos, use: [Recorte: Doc. ID XXX, fl. N - descricao]
- Identifique cada documento por seu ID unico e paginas

PRINCIPIOS:
- Jurisprudencia > Opiniao (sempre fundamentar com precedentes)
- Redacao juridica tecnica e precisa
- Conformidade CNJ obrigatoria
- Citacoes qualificadas (ratio decidendi identificada)"""


def welcome_message() -> str:
    return """Bem-vindo ao **Legal Analyst Squad**.

Sou o **@legal-chief**, orquestrador do pipeline de analise juridica. Tenho a disposicao 15 agentes especializados para oferecer suporte completo na analise processual.

**Como posso ajudar:**

1. **Envie um PDF** de processo judicial para analise completa
2. **Descreva sua demanda** (ex: "elaborar contrarrazoes", "analisar jurisprudencia sobre tema X")
3. **Adicione consideracoes** relevantes sobre o caso

**Comandos disponiveis:**
- `*intake` - Iniciar analise de processo via PDF
- `*relatorio` - Gerar relatorio estrategico
- `*minutar` - Elaborar peca processual
- `*pesquisar` - Pesquisar jurisprudencia
- `*recortar` - Fazer recorte de documento
- `*agentes` - Ver agentes disponiveis

Qual e a sua demanda?"""


class SessionRepository:
    async def create_session(self, title: str = "Nova Analise", session_id: str | None = None) -> ChatSession:
        session_factory = _require_session_factory()
        new_session_id = session_id or str(uuid.uuid4())
        async with session_factory() as db:
            row = ChatSessionDB(session_id=new_session_id, title=title)
            db.add(row)
            db.add(ChatMessageDB(
                session_id=row.session_id,
                role=MessageRole.SYSTEM.value,
                content=system_prompt(),
                agent_name="sistema",
            ))
            db.add(ChatMessageDB(
                session_id=row.session_id,
                role=MessageRole.ASSISTANT.value,
                content=welcome_message(),
                agent_id="legal-chief",
                agent_name="@legal-chief",
            ))
            await db.commit()
        session = await self.get_session(row.session_id)
        assert session is not None
        return session

    async def ensure_session(self, session_id: str, title: str = "Analise recuperada") -> ChatSession:
        session = await self.get_session(session_id)
        if session:
            return session
        return await self.create_session(title=title, session_id=session_id)

    async def get_session(self, session_id: str) -> ChatSession | None:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(ChatSessionDB)
                .where(ChatSessionDB.session_id == session_id)
                .options(
                    selectinload(ChatSessionDB.messages),
                    selectinload(ChatSessionDB.documents),
                    selectinload(ChatSessionDB.clips),
                )
            )
            row = result.scalar_one_or_none()
            return _session_from_db(row) if row else None

    async def delete_session(self, session_id: str) -> bool:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            result = await db.execute(delete(ChatSessionDB).where(ChatSessionDB.session_id == session_id))
            await db.commit()
            return (result.rowcount or 0) > 0

    async def list_sessions(self) -> list[dict[str, Any]]:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(
                    ChatSessionDB,
                    func.count(func.distinct(ChatMessageDB.id)).label("message_count"),
                    func.count(func.distinct(DocumentDB.doc_id)).label("document_count"),
                )
                .outerjoin(ChatMessageDB, ChatMessageDB.session_id == ChatSessionDB.session_id)
                .outerjoin(DocumentDB, DocumentDB.session_id == ChatSessionDB.session_id)
                .group_by(ChatSessionDB.session_id)
                .order_by(ChatSessionDB.updated_at.desc())
            )
            rows = []
            for session, message_count, document_count in result.all():
                rows.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "phase": session.phase,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": int(message_count or 0),
                    "document_count": int(document_count or 0),
                })
            return rows

    async def add_user_message(
        self,
        session_id: str,
        content: str,
        considerations: str = "",
        references: list[DocumentReference] | None = None,
        attachments: list[str] | None = None,
    ) -> ChatMessage:
        return await self.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            considerations=considerations,
            references=references,
            attachments=attachments,
        )

    async def add_agent_response(
        self,
        session_id: str,
        content: str,
        agent_id: str,
        agent_name: str,
        references: list[DocumentReference] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        return await self.add_message(
            session_id=session_id,
            role=MessageRole.AGENT,
            content=content,
            agent_id=agent_id,
            agent_name=agent_name,
            references=references,
            metadata=metadata,
        )

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        considerations: str = "",
        agent_id: str | None = None,
        agent_name: str | None = None,
        references: list[DocumentReference] | None = None,
        attachments: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            session = await db.get(ChatSessionDB, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            if considerations:
                session.considerations = considerations
            session.updated_at = datetime.now()
            row = ChatMessageDB(
                session_id=session_id,
                role=role.value,
                content=content,
                agent_id=agent_id,
                agent_name=agent_name,
                attachments=attachments or [],
                references=[_reference_to_dict(ref) for ref in (references or [])],
                extra=metadata or {},
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return _message_from_db(row)

    async def update_phase(self, session_id: str, phase: SessionPhase) -> None:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            row = await db.get(ChatSessionDB, session_id)
            if row:
                row.phase = phase.value
                row.updated_at = datetime.now()
                await db.commit()


class DocumentRepository:
    async def add_document(self, filepath: Path, session_id: str | None = None) -> tuple[DocumentMetadata, list[DocumentPage]]:
        metadata, pages = extract_pdf(filepath)
        sha256 = hashlib.sha256(filepath.read_bytes()).hexdigest()
        session_factory = _require_session_factory()
        async with session_factory() as db:
            row = DocumentDB(
                doc_id=metadata.doc_id,
                session_id=session_id or None,
                filename=metadata.filename,
                title=metadata.title,
                stored_path=str(filepath),
                sha256=sha256,
                total_pages=metadata.total_pages,
                file_size_bytes=metadata.file_size_bytes,
                extracted_parties=metadata.extracted_parties,
                process_number=metadata.process_number,
                court=metadata.court,
                subject=metadata.subject,
                text_page_count=metadata.text_page_count,
                scanned_page_count=metadata.scanned_page_count,
                ocr_required=metadata.ocr_required,
                extraction_status=metadata.extraction_status,
                extraction_warnings=metadata.extraction_warnings,
            )
            db.add(row)
            for page in pages:
                db.add(DocumentPageDB(
                    doc_id=metadata.doc_id,
                    page_number=page.page_number,
                    text=page.text,
                    images=page.images,
                    word_count=page.word_count,
                    text_length=page.text_length,
                    image_count=page.image_count,
                    extraction_method=page.extraction_method,
                    extraction_status=page.extraction_status,
                    needs_ocr=page.needs_ocr,
                    ocr_status="pending" if page.needs_ocr else "not_required",
                ))
            await db.commit()
        return metadata, pages

    async def list_documents(self, session_id: str | None = None) -> list[DocumentMetadata]:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            stmt = select(DocumentDB).order_by(DocumentDB.created_at.desc())
            if session_id:
                stmt = stmt.where(DocumentDB.session_id == session_id)
            result = await db.execute(stmt)
            return [_document_from_db(row) for row in result.scalars().all()]

    async def get_document(self, doc_id: str) -> DocumentMetadata | None:
        row = await self._get_document_row(doc_id)
        return _document_from_db(row) if row else None

    async def get_pages(self, doc_id: str) -> list[DocumentPage]:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(DocumentPageDB)
                .where(DocumentPageDB.doc_id == doc_id)
                .order_by(DocumentPageDB.page_number)
            )
            return [_page_from_db(row) for row in result.scalars().all()]

    async def get_page(self, doc_id: str, page_number: int) -> DocumentPage | None:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            result = await db.execute(
                select(DocumentPageDB)
                .where(DocumentPageDB.doc_id == doc_id, DocumentPageDB.page_number == page_number)
            )
            row = result.scalar_one_or_none()
            return _page_from_db(row) if row else None

    async def get_page_thumbnail(self, doc_id: str, page_number: int) -> str:
        row = await self._get_document_row(doc_id)
        if not row or not row.stored_path:
            return ""
        return get_page_thumbnail(Path(row.stored_path), page_number)

    async def create_clip(
        self,
        doc_id: str,
        page_start: int,
        page_end: int | None = None,
        x0: float = 0,
        y0: float = 0,
        x1: float = 0,
        y1: float = 0,
        clip_type: DocumentRefType = DocumentRefType.EXCERPT,
        label: str = "",
        session_id: str | None = None,
    ) -> DocumentClip | None:
        row = await self._get_document_row(doc_id)
        if not row or not row.stored_path:
            return None
        clip = clip_region(Path(row.stored_path), page_start, page_end, x0, y0, x1, y1, clip_type, label)
        clip.doc_id = doc_id
        session_factory = _require_session_factory()
        async with session_factory() as db:
            db.add(DocumentClipDB(
                clip_id=clip.clip_id,
                session_id=session_id or row.session_id,
                doc_id=doc_id,
                page_start=clip.page_start,
                page_end=clip.page_end,
                x0=clip.x0,
                y0=clip.y0,
                x1=clip.x1,
                y1=clip.y1,
                clip_type=clip.clip_type.value,
                content_text=clip.content_text,
                image_path=clip.image_path,
                label=clip.label,
            ))
            await db.commit()
        return clip

    async def get_clip(self, clip_id: str) -> DocumentClip | None:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            row = await db.get(DocumentClipDB, clip_id)
            return _clip_from_db(row) if row else None

    async def list_clips(self, doc_id: str | None = None) -> list[DocumentClip]:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            stmt = select(DocumentClipDB).order_by(DocumentClipDB.created_at.desc())
            if doc_id:
                stmt = stmt.where(DocumentClipDB.doc_id == doc_id)
            result = await db.execute(stmt)
            return [_clip_from_db(row) for row in result.scalars().all()]

    async def search(self, doc_id: str, query: str) -> list[dict[str, Any]]:
        pages = await self.get_pages(doc_id)
        if not pages:
            return []
        results: list[dict[str, Any]] = []
        query_lower = query.lower()
        for page in pages:
            text = page.text or ""
            match_at = text.lower().find(query_lower)
            if match_at < 0:
                continue
            start = max(0, match_at - 100)
            end = min(len(text), match_at + len(query) + 200)
            results.append({
                "page": page.page_number,
                "rect": [],
                "context": text[start:end].strip(),
                "source": page.extraction_method,
            })
        return results

    async def resolve_reference(self, ref: DocumentReference) -> dict[str, Any]:
        result: dict[str, Any] = {"ref": ref.model_dump(), "content": ""}
        if ref.clip_id:
            clip = await self.get_clip(ref.clip_id)
            if clip:
                result["content"] = clip.content_text
                result["image_path"] = clip.image_path
                result["label"] = clip.label
            return result
        if ref.page is not None:
            page = await self.get_page(ref.doc_id, ref.page)
            if page:
                result["content"] = page.text
            return result
        if ref.page_range:
            parts = ref.page_range.split("-")
            if len(parts) == 2:
                start, end = int(parts[0]), int(parts[1])
                texts = []
                for pn in range(start, end + 1):
                    page = await self.get_page(ref.doc_id, pn)
                    if page:
                        texts.append(f"--- Pagina {pn} ---\n{page.text}")
                result["content"] = "\n\n".join(texts)
        return result

    async def build_remissao_text(self, ref: DocumentReference) -> str:
        doc = await self.get_document(ref.doc_id)
        if not doc:
            return ""
        doc_label = ref.label or doc.filename
        if ref.clip_id:
            clip = await self.get_clip(ref.clip_id)
            if clip:
                return f"(Doc. ID {doc.doc_id} - {clip.label}, fls. {clip.page_start}" + (
                    f"-{clip.page_end}" if clip.page_end != clip.page_start else ""
                ) + ")"
        if ref.page is not None:
            return f"(Doc. ID {doc.doc_id} - {doc_label}, fl. {ref.page})"
        if ref.page_range:
            return f"(Doc. ID {doc.doc_id} - {doc_label}, fls. {ref.page_range})"
        return f"(Doc. ID {doc.doc_id} - {doc_label})"

    async def _get_document_row(self, doc_id: str) -> DocumentDB | None:
        session_factory = _require_session_factory()
        async with session_factory() as db:
            return await db.get(DocumentDB, doc_id)


session_repository = SessionRepository()
document_repository = DocumentRepository()
