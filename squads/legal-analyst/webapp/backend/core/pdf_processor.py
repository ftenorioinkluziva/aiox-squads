"""PDF processing: extraction, clipping, image capture, cross-referencing."""
from __future__ import annotations

import base64
import io
import re
import uuid
from pathlib import Path

import fitz  # PyMuPDF

from .config import CLIPS_DIR, UPLOAD_DIR
from .models import DocumentClip, DocumentMetadata, DocumentPage, DocumentRefType


_OCR_ENGINE = None
_OCR_ENGINE_FAILED = False


def extract_pdf(filepath: Path) -> tuple[DocumentMetadata, list[DocumentPage]]:
    """Extract full PDF content: text, images, metadata."""
    doc = fitz.open(str(filepath))
    pages: list[DocumentPage] = []
    all_text = ""
    text_page_count = 0
    scanned_page_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        extraction_method = "text"

        image_paths: list[str] = []
        for img_idx, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            if base_image:
                img_filename = f"{filepath.stem}_p{page_num + 1}_img{img_idx}.{base_image['ext']}"
                img_path = CLIPS_DIR / img_filename
                img_path.write_bytes(base_image["image"])
                image_paths.append(str(img_path))

        text_length = len(text)
        image_count = len(image_paths)
        if text_length < 50:
            ocr_text = _ocr_page(page)
            if len(ocr_text) > text_length:
                text = ocr_text
                text_length = len(text)
                extraction_method = "ocr"

        all_text += text

        needs_ocr = text_length < 50
        extraction_status = "ocr_required" if needs_ocr else "extracted"
        if needs_ocr:
            extraction_method = "image" if image_count > 0 else "ocr_unavailable"

        if text_length >= 50:
            text_page_count += 1
        elif needs_ocr:
            scanned_page_count += 1

        pages.append(DocumentPage(
            page_number=page_num + 1,
            text=text,
            images=image_paths,
            word_count=len(text.split()),
            text_length=text_length,
            image_count=image_count,
            extraction_method=extraction_method,
            extraction_status=extraction_status,
            needs_ocr=needs_ocr,
        ))

    extraction_warnings = _build_extraction_warnings(
        total_pages=len(doc),
        text_page_count=text_page_count,
        scanned_page_count=scanned_page_count,
        all_text=all_text,
    )
    extraction_status = _resolve_extraction_status(
        total_pages=len(doc),
        text_page_count=text_page_count,
        scanned_page_count=scanned_page_count,
    )

    metadata = DocumentMetadata(
        filename=filepath.name,
        title=doc.metadata.get("title", filepath.stem) or filepath.stem,
        total_pages=len(doc),
        file_size_bytes=filepath.stat().st_size,
        process_number=_extract_process_number(all_text),
        extracted_parties=_extract_parties(all_text),
        court=_extract_court(all_text),
        subject=_extract_subject(all_text),
        text_page_count=text_page_count,
        scanned_page_count=scanned_page_count,
        ocr_required=scanned_page_count > 0,
        extraction_status=extraction_status,
        extraction_warnings=extraction_warnings,
    )

    doc.close()
    return metadata, pages


def _resolve_extraction_status(
    total_pages: int,
    text_page_count: int,
    scanned_page_count: int,
) -> str:
    if total_pages == 0:
        return "empty"
    if text_page_count == 0 and scanned_page_count > 0:
        return "ocr_required"
    if scanned_page_count > 0:
        return "partial"
    return "extracted"


def _ocr_page(page: fitz.Page) -> str:
    """Run OCR on a PDF page when an optional OCR engine is available."""
    ocr_engine = _get_ocr_engine()
    if not ocr_engine:
        return ""

    try:
        pix = page.get_pixmap(dpi=220, alpha=False)
        image = _pixmap_to_image_array(pix)
        result, _elapsed = ocr_engine(image)
    except Exception:
        return ""

    if not result:
        return ""

    lines: list[str] = []
    for item in result:
        if len(item) < 2:
            continue
        text = str(item[1]).strip()
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def _get_ocr_engine():
    """Load RapidOCR lazily so the app still works when OCR deps are absent."""
    global _OCR_ENGINE, _OCR_ENGINE_FAILED
    if _OCR_ENGINE or _OCR_ENGINE_FAILED:
        return _OCR_ENGINE

    try:
        from rapidocr_onnxruntime import RapidOCR

        _OCR_ENGINE = RapidOCR()
    except Exception:
        _OCR_ENGINE_FAILED = True
        return None

    return _OCR_ENGINE


def _pixmap_to_image_array(pix: fitz.Pixmap):
    from PIL import Image
    import numpy as np

    image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    return np.array(image)


def _build_extraction_warnings(
    total_pages: int,
    text_page_count: int,
    scanned_page_count: int,
    all_text: str,
) -> list[str]:
    warnings: list[str] = []
    if scanned_page_count:
        warnings.append(
            f"{scanned_page_count} de {total_pages} pagina(s) parecem escaneadas e precisam de OCR."
        )
    if total_pages and text_page_count == 0:
        warnings.append(
            "Nenhum texto selecionavel foi encontrado. A analise automatica fica limitada ate o OCR ser aplicado."
        )
    if all_text and not _extract_process_number(all_text):
        warnings.append("Numero do processo nao identificado automaticamente.")
    if all_text and not _extract_court(all_text):
        warnings.append("Tribunal ou vara nao identificado automaticamente.")
    if all_text and not _extract_parties(all_text):
        warnings.append("Partes nao identificadas automaticamente.")
    return warnings


def clip_region(
    filepath: Path,
    page_start: int,
    page_end: int | None,
    x0: float, y0: float, x1: float, y1: float,
    clip_type: DocumentRefType,
    label: str = "",
) -> DocumentClip:
    """Extract a clip (text excerpt or image region) from the PDF."""
    doc = fitz.open(str(filepath))
    end = page_end or page_start
    clip_id = str(uuid.uuid4())[:8]
    content_parts: list[str] = []
    image_path = None

    for pn in range(page_start - 1, min(end, len(doc))):
        page = doc[pn]

        if x1 > 0 and y1 > 0:
            rect = fitz.Rect(x0, y0, x1, y1)
        else:
            rect = page.rect

        if clip_type == DocumentRefType.IMAGE:
            pix = page.get_pixmap(clip=rect, dpi=200)
            img_filename = f"clip_{clip_id}_p{pn + 1}.png"
            img_path = CLIPS_DIR / img_filename
            pix.save(str(img_path))
            image_path = str(img_path)
        else:
            text = page.get_text("text", clip=rect)
            content_parts.append(text.strip())

    doc.close()

    return DocumentClip(
        clip_id=clip_id,
        doc_id="",
        page_start=page_start,
        page_end=end,
        x0=x0, y0=y0, x1=x1, y1=y1,
        clip_type=clip_type,
        content_text="\n\n".join(content_parts),
        image_path=image_path,
        label=label or f"Recorte p.{page_start}" + (f"-{end}" if end != page_start else ""),
    )


def get_page_thumbnail(filepath: Path, page_number: int, width: int = 400) -> str:
    """Generate a base64-encoded thumbnail for a specific page."""
    doc = fitz.open(str(filepath))
    if page_number < 1 or page_number > len(doc):
        doc.close()
        return ""
    page = doc[page_number - 1]
    zoom = width / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return base64.b64encode(img_bytes).decode("utf-8")


def search_in_document(filepath: Path, query: str) -> list[dict]:
    """Search for text across all pages, returning matches with page numbers."""
    doc = fitz.open(str(filepath))
    results = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text_instances = page.search_for(query)
        if text_instances:
            context = page.get_text("text")
            for inst in text_instances:
                start = max(0, context.lower().find(query.lower()) - 100)
                end = min(len(context), start + len(query) + 200)
                results.append({
                    "page": page_num + 1,
                    "rect": [inst.x0, inst.y0, inst.x1, inst.y1],
                    "context": context[start:end].strip(),
                })
    doc.close()
    return results


# ---------------------------------------------------------------------------
# Private helpers: regex-based extraction from legal documents
# ---------------------------------------------------------------------------

def _extract_process_number(text: str) -> str:
    pattern = r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"
    match = re.search(pattern, text)
    return match.group(0) if match else ""


def _extract_parties(text: str) -> list[str]:
    parties = []
    patterns = [
        r"(?:AUTOR|REQUERENTE|RECLAMANTE|IMPETRANTE)[:\s]+([^\n]{5,80})",
        r"(?:REU|REQUERIDO|RECLAMADO|IMPETRADO)[:\s]+([^\n]{5,80})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            parties.append(m.group(1).strip())
    return parties


def _extract_court(text: str) -> str:
    patterns = [
        r"(TRIBUNAL\s+(?:DE\s+)?(?:JUSTICA|REGIONAL)\s+[^\n]{5,60})",
        r"(STF|STJ|TST|TRF\d?|TRT\d?|TJSP|TJRJ|TJMG|TJRS|TJPR|TJSC|TJBA|TJPE|TJCE|TJDF)",
        r"(\d+[aª]\s+(?:VARA|TURMA|CAMARA)[^\n]{5,60})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _extract_subject(text: str) -> str:
    patterns = [
        r"(?:ASSUNTO|MATERIA|CLASSE)[:\s]+([^\n]{5,120})",
        r"(?:ACAO\s+DE|RECURSO\s+DE|MANDADO\s+DE)[:\s]*([^\n]{5,80})",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""
