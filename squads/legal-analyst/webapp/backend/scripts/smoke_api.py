r"""Smoke checks for the local Legal Analyst API.

Run with the backend already started:

    .\.venv\Scripts\python.exe scripts\smoke_api.py

Optional environment variables:

    LEGAL_ANALYST_API_BASE=http://127.0.0.1:8000
    LEGAL_ANALYST_TEST_PDF=C:\Users\fteno\Downloads\BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx


API_BASE = os.getenv("LEGAL_ANALYST_API_BASE", "http://127.0.0.1:8000")
DEFAULT_TEST_PDF = r"C:\Users\fteno\Downloads\BUSCA E APREENSÃO EM ALIENAÇÃO FIDUCIÁRIA (81).pdf"
TEST_PDF = Path(os.getenv("LEGAL_ANALYST_TEST_PDF", DEFAULT_TEST_PDF))


def assert_ok(response: httpx.Response) -> dict:
    response.raise_for_status()
    return response.json()


def main() -> None:
    session_id = ""
    with httpx.Client(base_url=API_BASE, timeout=60) as client:
        try:
            health = assert_ok(client.get("/api/health"))
            assert health["status"] == "ok"

            session = assert_ok(client.post("/api/sessions", params={"title": "Smoke API"}))
            session_id = session["session_id"]
            assert session_id

            loaded = assert_ok(client.get(f"/api/sessions/{session_id}"))
            assert loaded["session_id"] == session_id
            assert loaded["messages"]

            agent_response = assert_ok(client.post("/api/chat", json={
                "session_id": session_id,
                "content": "*agentes",
            }))
            assert agent_response["agent_id"] == "legal-chief"

            if TEST_PDF.exists():
                with TEST_PDF.open("rb") as file_obj:
                    upload = assert_ok(client.post(
                        f"/api/documents/upload?session_id={session_id}",
                        files={"file": (TEST_PDF.name, file_obj, "application/pdf")},
                    ))
                doc_id = upload["doc_id"]
                assert doc_id

                document = assert_ok(client.get(f"/api/documents/{doc_id}"))
                assert document["doc_id"] == doc_id

                page = assert_ok(client.get(f"/api/documents/{doc_id}/pages/1"))
                assert page["page_number"] == 1

                if document["ocr_required"]:
                    pipeline = assert_ok(client.post("/api/pipelines/start", json={
                        "session_id": session_id,
                        "workflow_id": "wf-analise-processual-completa",
                    }))
                    assert pipeline["status"] == "blocked"
                    assert "OCR pendente" in (pipeline.get("error_message") or "")

            reloaded = assert_ok(client.get(f"/api/sessions/{session_id}"))
            assert reloaded["session_id"] == session_id
        finally:
            if session_id:
                client.delete(f"/api/sessions/{session_id}")

    print("smoke api ok")


if __name__ == "__main__":
    main()
