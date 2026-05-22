"""Persistent execution engine for Legal Analyst workflow pipelines."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .config import WORKFLOWS_DIR
from .db import SessionLocal, require_database
from .llm_provider import LLMConfigurationError, build_legal_system_prompt, generate_text
from .models import SessionPhase
from .pipeline_db import PipelineEventDB, PipelineOutputDB, PipelineRunDB, PipelineStepDB
from .pipeline_realtime import pipeline_hub
from .repositories import document_repository, session_repository

RUN_ACTIVE_STATUSES = {"queued", "running"}
TERMINAL_STATUSES = {"completed", "failed", "blocked"}

TASK_AGENT_MAP = {
    "classificar-processo": "barbosa-classifier",
    "verificar-admissibilidade": "fux-procedural",
    "carregar-cnj": "cnj-compliance",
    "pesquisar-jurisprudencia": "mendes-researcher",
    "consolidar-precedentes": "toffoli-aggregator",
    "analisar-direitos-fundamentais": "moraes-analyst",
    "indexar-jurisprudencia": "weber-indexer",
    "analisar-precedentes": "fachin-precedent",
    "jurimetria": "nunes-quantitative",
    "perfil-relatores": "carmem-relator",
    "linhas-argumentativas": "barroso-strategist",
    "estrategia-argumentativa": "barroso-strategist",
    "qualificar-citacoes": "fachin-precedent",
    "validar-fundamentacao": "theodoro-validator",
    "validar-precedentes": "marinoni-quality",
    "validar-cnj": "cnj-compliance",
    "formatar-datajud": "datajud-formatter",
    "montar-relatorio": "legal-chief",
    "armazenar-dominio": "datajud-formatter",
}


def _load_workflow(workflow_id: str) -> dict[str, Any]:
    for wf_file in WORKFLOWS_DIR.glob("*.yaml"):
        data = yaml.safe_load(wf_file.read_text(encoding="utf-8"))
        workflow = data.get("workflow", {})
        if workflow.get("id") == workflow_id or workflow_id in wf_file.stem:
            return data
    raise ValueError(f"Workflow {workflow_id} nao encontrado")


async def _build_document_context(session: Any) -> str:
    parts = []
    for doc in session.documents:
        pages = await document_repository.get_pages(doc.doc_id)
        parts.append(
            f"Doc. ID {doc.doc_id} - {doc.filename}\n"
            f"Processo: {doc.process_number or 'N/I'} | Tribunal: {doc.court or 'N/I'} | "
            f"Partes: {', '.join(doc.extracted_parties) or 'N/I'}"
        )
        for page in pages[:8]:
            parts.append(f"--- Pagina {page.page_number} ---\n{page.text[:3000]}")
    return "\n\n".join(parts)


def _serialize_dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_step(step: PipelineStepDB) -> dict[str, Any]:
    return {
        "id": step.id,
        "run_id": step.run_id,
        "phase_id": step.phase_id,
        "phase_name": step.phase_name,
        "task_id": step.task_id,
        "task_description": step.task_description,
        "agent_id": step.agent_id,
        "status": step.status,
        "dependencies": step.dependencies or [],
        "output_text": step.output_text,
        "error_message": step.error_message,
        "sort_order": step.sort_order,
        "started_at": _serialize_dt(step.started_at),
        "completed_at": _serialize_dt(step.completed_at),
    }


def serialize_event(event: PipelineEventDB) -> dict[str, Any]:
    return {
        "id": event.id,
        "run_id": event.run_id,
        "event_type": event.event_type,
        "message": event.message,
        "payload": event.payload or {},
        "created_at": _serialize_dt(event.created_at),
    }


def serialize_run(run: PipelineRunDB) -> dict[str, Any]:
    output = run.outputs[-1].content_md if run.outputs else None
    return {
        "id": run.id,
        "session_id": run.session_id,
        "workflow_id": run.workflow_id,
        "status": run.status,
        "current_phase_id": run.current_phase_id,
        "error_message": run.error_message,
        "created_at": _serialize_dt(run.created_at),
        "updated_at": _serialize_dt(run.updated_at),
        "completed_at": _serialize_dt(run.completed_at),
        "steps": [serialize_step(step) for step in run.steps],
        "events": [serialize_event(event) for event in run.events],
        "output_md": output,
    }


async def _load_run(session, run_id: str) -> PipelineRunDB | None:
    result = await session.execute(
        select(PipelineRunDB)
        .where(PipelineRunDB.id == run_id)
        .options(
            selectinload(PipelineRunDB.steps),
            selectinload(PipelineRunDB.events),
            selectinload(PipelineRunDB.outputs),
        )
    )
    return result.scalar_one_or_none()


async def get_pipeline(run_id: str) -> dict[str, Any] | None:
    require_database()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        return serialize_run(run) if run else None


async def get_latest_pipeline(session_id: str) -> dict[str, Any] | None:
    require_database()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        result = await session.execute(
            select(PipelineRunDB)
            .where(PipelineRunDB.session_id == session_id)
            .order_by(PipelineRunDB.created_at.desc())
            .limit(1)
        )
        run = result.scalar_one_or_none()
        if not run:
            return None
        return await get_pipeline(run.id)


async def mark_interrupted_runs() -> None:
    if SessionLocal is None:
        return
    async with SessionLocal() as session:
        result = await session.execute(
            select(PipelineRunDB).where(PipelineRunDB.status.in_(RUN_ACTIVE_STATUSES))
        )
        runs = result.scalars().all()
        for run in runs:
            run.status = "failed"
            run.error_message = "Execucao interrompida por reinicio do backend; inicie uma nova analise."
            run.completed_at = datetime.utcnow()
            await _add_event(session, run.id, "run_failed", run.error_message)
        await session.commit()


async def _add_event(session, run_id: str, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
    event = PipelineEventDB(
        run_id=run_id,
        event_type=event_type,
        message=message,
        payload=payload or {},
    )
    session.add(event)
    await session.flush()
    serialized = serialize_event(event)
    await pipeline_hub.publish(run_id, serialized)


async def start_pipeline(session_id: str, workflow_id: str = "wf-analise-processual-completa") -> dict[str, Any]:
    require_database()
    assert SessionLocal is not None
    chat_session = await session_repository.get_session(session_id)
    if not chat_session:
        raise ValueError("Sessao nao encontrada")
    if not chat_session.documents:
        raise ValueError("Envie ao menos um PDF antes de iniciar a analise")

    async with SessionLocal() as session:
        existing = await session.execute(
            select(PipelineRunDB)
            .where(PipelineRunDB.session_id == session_id, PipelineRunDB.status.in_(RUN_ACTIVE_STATUSES))
            .order_by(PipelineRunDB.created_at.desc())
            .limit(1)
        )
        active = existing.scalar_one_or_none()
        if active:
            loaded = await _load_run(session, active.id)
            return serialize_run(loaded)

        workflow = _load_workflow(workflow_id)
        run = PipelineRunDB(session_id=session_id, workflow_id=workflow_id, status="queued")
        session.add(run)
        await session.flush()

        docs_requiring_ocr = [doc.filename for doc in chat_session.documents if getattr(doc, "ocr_required", False)]
        if docs_requiring_ocr:
            run.status = "blocked"
            run.error_message = "OCR pendente nos documentos: " + ", ".join(docs_requiring_ocr)
            run.completed_at = datetime.utcnow()
            await _add_event(session, run.id, "run_blocked", run.error_message, {"documents": docs_requiring_ocr})
            await session.commit()
            loaded = await _load_run(session, run.id)
            return serialize_run(loaded)

        sort_order = 0
        for phase in workflow.get("phases", []):
            phase_agents = phase.get("agents", [])
            for task in phase.get("tasks", []):
                task_id = task["id"]
                step = PipelineStepDB(
                    run_id=run.id,
                    phase_id=phase["id"],
                    phase_name=phase["name"],
                    task_id=task_id,
                    task_description=task.get("description", task_id),
                    agent_id=TASK_AGENT_MAP.get(task_id, phase_agents[0] if phase_agents else "legal-chief"),
                    dependencies=task.get("dependencies", []),
                    sort_order=sort_order,
                )
                sort_order += 1
                session.add(step)

        await _add_event(session, run.id, "run_started", "Pipeline de analise iniciado", {"workflow_id": workflow_id})
        await session.commit()
        loaded = await _load_run(session, run.id)
        return serialize_run(loaded)


def schedule_pipeline(run_id: str) -> None:
    asyncio.create_task(run_pipeline(run_id))


async def run_pipeline(run_id: str) -> None:
    require_database()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        if not run or run.status != "queued":
            return
        run.status = "running"
        await _add_event(session, run_id, "run_running", "Pipeline em execucao")
        await session.commit()

    while True:
        async with SessionLocal() as session:
            run = await _load_run(session, run_id)
            if not run or run.status in TERMINAL_STATUSES:
                return
            phase_ids = []
            for step in run.steps:
                if step.phase_id not in phase_ids:
                    phase_ids.append(step.phase_id)

        for phase_id in phase_ids:
            should_continue = await _run_phase(run_id, phase_id)
            if not should_continue:
                return

        await _complete_run(run_id)
        return


async def _run_phase(run_id: str, phase_id: str) -> bool:
    assert SessionLocal is not None
    while True:
        async with SessionLocal() as session:
            run = await _load_run(session, run_id)
            if not run or run.status in TERMINAL_STATUSES:
                return False
            run.current_phase_id = phase_id
            phase_steps = [step for step in run.steps if step.phase_id == phase_id]
            if all(step.status == "completed" for step in phase_steps):
                await session.commit()
                return True
            failed = next((step for step in phase_steps if step.status == "failed"), None)
            if failed:
                run.status = "failed"
                run.error_message = failed.error_message
                run.completed_at = datetime.utcnow()
                await _add_event(session, run_id, "run_failed", failed.error_message or "Falha no pipeline")
                await session.commit()
                return False

            completed_task_ids = {step.task_id for step in phase_steps if step.status == "completed"}
            ready = [
                step
                for step in phase_steps
                if step.status == "queued" and all(dep in completed_task_ids for dep in (step.dependencies or []))
            ]
            if not ready:
                run.status = "blocked"
                run.error_message = f"Dependencias pendentes ou ciclo detectado na fase {phase_id}"
                run.completed_at = datetime.utcnow()
                await _add_event(session, run_id, "run_blocked", run.error_message)
                await session.commit()
                return False
            await session.commit()

        await asyncio.gather(*[_execute_step(run_id, step.id) for step in ready])


async def _execute_step(run_id: str, step_id: str) -> None:
    assert SessionLocal is not None
    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        step = next((item for item in run.steps if item.id == step_id), None) if run else None
        if not run or not step or step.status != "queued":
            return
        step.status = "running"
        step.started_at = datetime.utcnow()
        await _add_event(
            session,
            run_id,
            "step_started",
            f"{step.agent_id} iniciou {step.task_id}",
            {"step_id": step.id, "agent_id": step.agent_id, "task_id": step.task_id},
        )
        await session.commit()

    try:
        output = await _call_step_llm(run_id, step_id)
    except LLMConfigurationError as exc:
        output = None
        error = str(exc)
    except Exception as exc:
        output = None
        error = f"Falha tecnica no step {step_id}: {exc}"
    else:
        error = None

    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        step = next((item for item in run.steps if item.id == step_id), None) if run else None
        if not step:
            return
        if error:
            step.status = "failed"
            step.error_message = error
            await _add_event(session, run_id, "step_failed", error, {"step_id": step.id, "task_id": step.task_id})
        else:
            step.status = "completed"
            step.output_text = output
            step.completed_at = datetime.utcnow()
            await _add_event(
                session,
                run_id,
                "step_completed",
                f"{step.agent_id} concluiu {step.task_id}",
                {"step_id": step.id, "agent_id": step.agent_id, "task_id": step.task_id},
            )
        await session.commit()


async def _call_step_llm(run_id: str, step_id: str) -> str:
    assert SessionLocal is not None
    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        step = next((item for item in run.steps if item.id == step_id), None) if run else None
        if not run or not step:
            raise ValueError("Step nao encontrado")
        chat_session = await session_repository.get_session(run.session_id)
        if not chat_session:
            raise ValueError("Sessao nao encontrada")
        doc_context = await _build_document_context(chat_session)
        completed_outputs = [
            f"## {item.task_id} ({item.agent_id})\n{item.output_text}"
            for item in run.steps
            if item.status == "completed" and item.output_text
        ]
        extra_context = "\n\n".join(completed_outputs[-8:])
        user_prompt = f"""Execute a tarefa do pipeline juridico.

Fase: {step.phase_name}
Tarefa: {step.task_id}
Descricao: {step.task_description}

Entregue uma resposta objetiva, estruturada em Markdown, com conclusoes, ressalvas e evidencias usadas. Se identificar bloqueio juridico ou documental, declare explicitamente no inicio com "BLOQUEIO:"."""

    system_prompt = build_legal_system_prompt(
        agent_id=step.agent_id,
        doc_context=doc_context,
        considerations=chat_session.considerations,
        extra_context=extra_context,
    )
    result = await generate_text(system_prompt=system_prompt, messages=[{"role": "user", "content": user_prompt}])
    if result.text.strip().upper().startswith("BLOQUEIO:"):
        raise ValueError(result.text.strip())
    return result.text


async def _complete_run(run_id: str) -> None:
    assert SessionLocal is not None
    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        if not run:
            return
        grouped: dict[str, list[PipelineStepDB]] = defaultdict(list)
        for step in run.steps:
            grouped[step.phase_name].append(step)

        sections = ["# Relatorio Consolidado - Legal Analyst Squad"]
        for phase_name, steps in grouped.items():
            sections.append(f"\n## {phase_name}")
            for step in steps:
                sections.append(f"\n### {step.task_id} - @{step.agent_id}\n{step.output_text or '*Sem saida registrada.*'}")
        content_md = "\n".join(sections)
        session.add(PipelineOutputDB(run_id=run_id, content_md=content_md))
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.current_phase_id = "phase_5_entrega"
        await _add_event(session, run_id, "run_completed", "Pipeline concluido", {"output": "markdown"})
        await session.commit()

        await session_repository.update_phase(run.session_id, SessionPhase.ENTREGA)
        await session_repository.add_agent_response(
            session_id=run.session_id,
            content=content_md,
            agent_id="legal-chief",
            agent_name="@legal-chief",
            metadata={"intent": "pipeline", "phase": "entrega", "pipeline_run_id": run_id},
        )
