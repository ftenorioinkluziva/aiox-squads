"""Agent orchestration engine: routes requests, manages agent pipeline, generates responses."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from .llm_provider import build_legal_system_prompt, generate_text
from .models import (
    ChatMessage,
    DocumentReference,
    MessageRole,
    SessionPhase,
)
from .repositories import document_repository, session_repository

logger = logging.getLogger(__name__)


# Agent routing rules based on intent detection
AGENT_ROUTING: dict[str, dict[str, Any]] = {
    "classificar": {"agent_id": "barbosa-classifier", "phase": SessionPhase.TRIAGEM},
    "admissibilidade": {"agent_id": "fux-procedural", "phase": SessionPhase.TRIAGEM},
    "compliance": {"agent_id": "cnj-compliance", "phase": SessionPhase.TRIAGEM},
    "pesquisar": {"agent_id": "mendes-researcher", "phase": SessionPhase.PESQUISA},
    "jurisprudencia": {"agent_id": "mendes-researcher", "phase": SessionPhase.PESQUISA},
    "precedente": {"agent_id": "fachin-precedent", "phase": SessionPhase.PESQUISA},
    "consolidar": {"agent_id": "toffoli-aggregator", "phase": SessionPhase.PESQUISA},
    "relator": {"agent_id": "carmem-relator", "phase": SessionPhase.ANALISE},
    "jurimetria": {"agent_id": "nunes-quantitative", "phase": SessionPhase.ANALISE},
    "direitos fundamentais": {"agent_id": "moraes-analyst", "phase": SessionPhase.ANALISE},
    "estrategia": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "fundamentacao": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "minutar": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "contrarrazoes": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "recurso": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "peticao": {"agent_id": "barroso-strategist", "phase": SessionPhase.FUNDAMENTACAO},
    "validar": {"agent_id": "theodoro-validator", "phase": SessionPhase.VALIDACAO},
    "qualidade": {"agent_id": "marinoni-quality", "phase": SessionPhase.VALIDACAO},
    "datajud": {"agent_id": "datajud-formatter", "phase": SessionPhase.ENTREGA},
    "indexar": {"agent_id": "weber-indexer", "phase": SessionPhase.ENTREGA},
}


def detect_intent(content: str) -> tuple[str, str | None]:
    """Detect user intent and route to appropriate agent."""
    content_lower = content.lower()

    # Check for explicit commands
    cmd_match = re.match(r"\*(\w+)", content)
    if cmd_match:
        cmd = cmd_match.group(1)
        if cmd in ("intake", "analisar"):
            return "intake", "legal-chief"
        if cmd in ("relatorio", "report"):
            return "relatorio", "legal-chief"
        if cmd in ("minutar", "draft"):
            return "minutar", "barroso-strategist"
        if cmd in ("pesquisar", "search"):
            return "pesquisar", "mendes-researcher"
        if cmd in ("recortar", "clip"):
            return "recortar", None
        if cmd in ("agentes", "agents"):
            return "agentes", None

    # Keyword-based routing
    for keyword, routing in AGENT_ROUTING.items():
        if keyword in content_lower:
            return keyword, routing["agent_id"]

    # Default to chief for orchestration
    return "general", "legal-chief"


def route_to_phase(intent: str) -> SessionPhase:
    """Map intent to pipeline phase."""
    for keyword, routing in AGENT_ROUTING.items():
        if keyword == intent:
            return routing["phase"]
    return SessionPhase.INTAKE


async def process_message(
    session_id: str,
    content: str,
    considerations: str = "",
    references: list[DocumentReference] | None = None,
    target_agent: str | None = None,
) -> ChatMessage:
    """Process a user message through the agent pipeline."""

    # Add user message
    await session_repository.add_user_message(
        session_id=session_id,
        content=content,
        considerations=considerations,
        references=references,
    )

    session = await session_repository.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Detect intent and route
    intent, agent_id = detect_intent(content)
    if target_agent:
        agent_id = target_agent

    # Handle special intents
    if intent == "agentes":
        return await _handle_agents_list(session_id)

    if intent == "recortar":
        return await _handle_clip_instructions(session_id)

    # Update phase
    phase = route_to_phase(intent)
    await session_repository.update_phase(session_id, phase)
    session.phase = phase

    # Build agent response based on context
    response_content = await _generate_agent_response(
        session=session,
        intent=intent,
        agent_id=agent_id or "legal-chief",
        references=references,
    )

    return await session_repository.add_agent_response(
        session_id=session_id,
        content=response_content,
        agent_id=agent_id or "legal-chief",
        agent_name=f"@{agent_id or 'legal-chief'}",
        references=references,
        metadata={"intent": intent, "phase": phase.value},
    )


async def _build_document_context(session: Any) -> str:
    """Build document context string from session documents."""
    doc_context = ""
    if session.documents:
        for doc in session.documents:
            pages = await document_repository.get_pages(doc.doc_id)
            doc_context += f"\n**Doc. ID {doc.doc_id}** - {doc.filename}\n"
            doc_context += f"Processo: {doc.process_number or 'N/I'} | "
            doc_context += f"Tribunal: {doc.court or 'N/I'} | "
            doc_context += f"Partes: {', '.join(doc.extracted_parties) or 'N/I'}\n"
            # Include full text of first 5 pages for context
            if pages:
                for page in pages[:5]:
                    doc_context += f"\n--- Pagina {page.page_number} ---\n"
                    doc_context += page.text[:2000] + "\n"
    return doc_context


async def _build_reference_context(references: list[DocumentReference] | None) -> str:
    """Build reference context string from document references."""
    ref_context = ""
    if references:
        for ref in references:
            resolved = await document_repository.resolve_reference(ref)
            remissao = await document_repository.build_remissao_text(ref)
            if resolved.get("content"):
                ref_context += f"\n{remissao}:\n{resolved['content'][:1000]}\n"
    return ref_context


def _build_conversation_history(session: Any) -> list[dict[str, str]]:
    """Build conversation history for the API call (last 20 messages)."""
    messages = []
    recent = session.messages[-20:] if session.messages else []
    for msg in recent:
        role = "user" if msg.role == MessageRole.USER else "assistant"
        messages.append({"role": role, "content": msg.content})
    return messages


async def _generate_agent_response(
    session: Any,
    intent: str,
    agent_id: str,
    references: list[DocumentReference] | None = None,
) -> str:
    """Generate agent response via Anthropic API. Falls back to templates if no API key."""

    doc_context = await _build_document_context(session)
    ref_context = await _build_reference_context(references)

    try:
        return await _call_llm_api(
            session=session,
            intent=intent,
            agent_id=agent_id,
            doc_context=doc_context,
            ref_context=ref_context,
        )
    except Exception as e:
        logger.error("LLM API call failed, falling back to template: %s", e)

    # Fallback to template responses
    return _fallback_template_response(session, intent, doc_context, ref_context)


async def _call_llm_api(
    session: Any,
    intent: str,
    agent_id: str,
    doc_context: str,
    ref_context: str,
) -> str:
    """Call the configured LLM providers with agent-specific prompt and context."""
    system_prompt = build_legal_system_prompt(
        agent_id=agent_id,
        doc_context=doc_context,
        ref_context=ref_context,
        considerations=session.considerations,
    )
    history = _build_conversation_history(session)

    # If no history (or just the current message), create a user message from intent
    if not history:
        history = [{"role": "user", "content": f"*{intent}"}]

    # Ensure messages alternate properly (API requirement)
    clean_messages = []
    last_role = None
    for msg in history:
        if msg["role"] == last_role:
            # Merge consecutive same-role messages
            clean_messages[-1]["content"] += "\n\n" + msg["content"]
        else:
            clean_messages.append(msg)
            last_role = msg["role"]

    # Ensure first message is from user
    if clean_messages and clean_messages[0]["role"] != "user":
        clean_messages.insert(0, {"role": "user", "content": f"*{intent}"})

    result = await generate_text(system_prompt=system_prompt, messages=clean_messages)
    return result.text


def _fallback_template_response(
    session: Any, intent: str, doc_context: str, ref_context: str,
) -> str:
    """Fallback to template responses when API is unavailable."""
    if intent == "intake":
        return _response_intake(session, doc_context)
    elif intent == "relatorio":
        return _response_relatorio(session, doc_context, ref_context)
    elif intent in ("minutar", "contrarrazoes", "recurso", "peticao"):
        return _response_minutar(session, intent, doc_context, ref_context)
    elif intent in ("pesquisar", "jurisprudencia", "precedente"):
        return _response_pesquisa(session, doc_context)
    elif intent in ("relator",):
        return _response_relator(session, doc_context)
    elif intent in ("jurimetria",):
        return _response_jurimetria(session, doc_context)
    elif intent in ("classificar",):
        return _response_classificacao(session, doc_context)
    elif intent in ("estrategia", "fundamentacao"):
        return _response_estrategia(session, doc_context, ref_context)
    else:
        return _response_general(session, doc_context)


def _response_intake(session: Any, doc_context: str) -> str:
    if not session.documents:
        return """Para iniciar a analise, por favor envie o **PDF do processo judicial**.

Apos o upload, executarei automaticamente:
1. **Extracao** de dados (partes, pedidos, causa de pedir)
2. **Classificacao** TPU/SGT (@barbosa-classifier)
3. **Verificacao** de admissibilidade (@fux-procedural)
4. **Compliance** CNJ (@cnj-compliance)

Voce tambem pode adicionar **consideracoes** sobre o caso no painel lateral."""

    docs_requiring_ocr = [doc for doc in session.documents if getattr(doc, "ocr_required", False)]
    if docs_requiring_ocr:
        warnings = []
        for doc in docs_requiring_ocr:
            doc_warnings = getattr(doc, "extraction_warnings", []) or []
            warnings.extend(doc_warnings)
        warning_text = "\n".join(f"- {warning}" for warning in warnings[:4])
        return f"""**Documento recebido, mas a leitura automatica ainda esta incompleta.**

{doc_context}

**O que aconteceu**
{warning_text or '- O documento parece escaneado e precisa de OCR.'}

**Proximo passo tecnico:** aplicar OCR nas paginas marcadas antes da triagem juridica completa.

Enquanto isso, voce pode informar em linguagem simples o que deseja fazer com o caso, por exemplo:
- entender do que se trata;
- avaliar risco;
- preparar defesa ou contestacao;
- gerar resumo para advogado.

O que voce quer descobrir primeiro sobre este processo?"""

    return f"""**Processo recebido e processado com sucesso.**

{doc_context}

**Pipeline de Triagem iniciado.** Os seguintes agentes foram acionados:

| Agente | Funcao | Status |
|--------|--------|--------|
| @barbosa-classifier | Classificacao TPU/SGT | Em andamento |
| @fux-procedural | Admissibilidade CPC | Em andamento |
| @cnj-compliance | Conformidade CNJ | Em andamento |

**Proximo passo:** Aguarde a triagem ou adicione **consideracoes** sobre sua demanda (ex: "elaborar contrarrazoes", "analisar viabilidade de recurso").

O que deseja que eu priorize na analise?"""


def _response_relatorio(session: Any, doc_context: str, ref_context: str) -> str:
    return f"""# RELATORIO ESTRATEGICO

## 1. Sintese Processual
{doc_context or '*Nenhum documento carregado. Envie o PDF para analise completa.*'}

## 2. Classificacao e Enquadramento
- **Classe Processual:** Pendente de classificacao TPU
- **Assuntos:** Pendente de indexacao SGT
- **Competencia:** A definir conforme tribunal

## 3. Analise de Viabilidade
> *Execute `*pesquisar` para analise jurisprudencial completa*

## 4. Mapeamento de Precedentes
> *Execute `*pesquisar jurisprudencia` para consolidacao de precedentes*

## 5. Perfil do Relator
> *Execute `*relator` para analise do perfil decisorio*

## 6. Jurimetria
> *Execute `*jurimetria` para dados quantitativos*

## 7. Estrategia Recomendada
> *Disponivel apos conclusao das fases 2-6*

{ref_context}

---
*Relatorio parcial. Para relatorio completo, execute cada fase ou use `*analisar` para pipeline automatico.*"""


def _response_minutar(session: Any, piece_type: str, doc_context: str, ref_context: str) -> str:
    piece_names = {
        "minutar": "Peca Processual",
        "contrarrazoes": "Contrarrazoes",
        "recurso": "Recurso",
        "peticao": "Peticao",
    }
    piece = piece_names.get(piece_type, "Peca Processual")

    return f"""## Minuta de {piece}

Para elaborar a minuta com a melhor redacao juridica, preciso:

1. **Documento base** carregado {('✓' if session.documents else '✗ *Envie o PDF*')}
2. **Consideracoes** do advogado {('✓' if session.considerations else '✗ *Adicione no painel*')}
3. **Recortes relevantes** selecionados {('✓' if session.clips else '✗ *Use o recorte de documentos*')}

{doc_context}

### Estrutura da {piece}:

**I. QUALIFICACAO DAS PARTES**
> Sera extraida automaticamente do documento

**II. SINTESE FATICA**
> Baseada na analise do processo + consideracoes

**III. PRELIMINARES** *(se aplicavel)*
> Analise de admissibilidade pelo @fux-procedural

**IV. MERITO**
> Fundamentacao qualificada conforme CPC Art. 489
> Com citacoes de precedentes (ratio decidendi)
> Remissao aos documentos: {ref_context or '*Selecione trechos relevantes*'}

**V. PEDIDOS**
> Conforme estrategia do @barroso-strategist

---
**Para prosseguir**, confirme o tipo de peca e forneca suas consideracoes.
Voce pode **recortar** trechos do documento para inserir no corpo da peca usando o painel de documentos."""


def _response_pesquisa(session: Any, doc_context: str) -> str:
    return """## Pesquisa Jurisprudencial

**Agentes acionados:**
- @mendes-researcher - Pesquisa constitucional e infraconstitucional
- @fachin-precedent - Analise de precedentes (distinguishing)
- @toffoli-aggregator - Consolidacao de resultados
- @marinoni-quality - Controle de qualidade dos precedentes

**Fontes consultadas:**
- STF, STJ, TST (precedentes vinculantes)
- TRFs e TJs (jurisprudencia dominante)
- Sumulas vinculantes e orientacoes jurisprudenciais
- IRDR e IAC aplicaveis

**Criterios de qualificacao:**
1. Ratio decidendi vs. obiter dictum
2. Vigencia e aplicabilidade
3. Similitude fatica (distinguishing)
4. Hierarquia jurisdicional

> *Indique o tema ou envie o documento para pesquisa automatica.*"""


def _response_relator(session: Any, doc_context: str) -> str:
    return """## Analise de Perfil do Relator

**@carmem-relator acionado.**

A analise incluira:
- **Historico decisorio** do Relator no tema
- **Tendencia** (deferimento/indeferimento)
- **Fundamentacao preferida** (principios, precedentes citados)
- **Peculiaridades** de estilo e exigencias processuais
- **Votos vencidos/vencedores** em temas correlatos

> *Identifique o Relator ou envie o documento para deteccao automatica.*"""


def _response_jurimetria(session: Any, doc_context: str) -> str:
    return """## Analise Jurimetrica

**@nunes-quantitative acionado.**

Dados a serem calculados:
- **Taxa de procedencia** no tema e tribunal
- **Valor medio/mediano** de condenacoes
- **Tempo medio** de tramitacao
- **Tendencia temporal** (crescente/decrescente/estavel)
- **Distribuicao por turma/camara**

> *Indique o tema e tribunal para analise quantitativa.*"""


def _response_classificacao(session: Any, doc_context: str) -> str:
    return f"""## Classificacao Processual

**@barbosa-classifier acionado.**

{doc_context}

Classificacao em andamento:
- **Classe processual** (TPU - Res. CNJ 396/2021)
- **Assuntos** (SGT - tabela unificada)
- **Competencia** (territorial, material, funcional)
- **Valor da causa** (verificacao)

> *Aguarde a classificacao ou foreca informacoes adicionais.*"""


def _response_estrategia(session: Any, doc_context: str, ref_context: str) -> str:
    return f"""## Estrategia Argumentativa

**@barroso-strategist acionado.**

{doc_context}

A estrategia sera construida em 3 camadas:

### Camada 1 - Fundamentacao Legal
- Dispositivos normativos aplicaveis
- Hierarquia normativa
- Vigencia e aplicabilidade

### Camada 2 - Fundamentacao Jurisprudencial
- Precedentes vinculantes
- Jurisprudencia dominante
- Distinguishing de precedentes desfavoraveis

### Camada 3 - Fundamentacao Fatica
- Subsuncao dos fatos a norma
- Provas documentais {ref_context or '*(selecione recortes)*'}
- Nexo causal e argumentacao logica

**Conformidade CPC Art. 489:**
- [ ] Indicacao de dispositivo legal
- [ ] Enfrentamento de argumentos contrarios
- [ ] Justificacao de aplicacao de precedente
- [ ] Fundamentacao nao generica

> *Forneca consideracoes ou selecione a linha argumentativa preferida.*"""


def _response_general(session: Any, doc_context: str) -> str:
    if not session.documents:
        return """Entendi sua solicitacao. Para melhor atende-lo, posso:

1. **Analisar processo** - Envie um PDF para analise completa
2. **Pesquisar jurisprudencia** - Sobre qualquer tema juridico
3. **Elaborar pecas** - Minutar documentos processuais
4. **Gerar relatorio** - Relatorio estrategico completo

Como deseja prosseguir?"""

    return f"""Analise em andamento com os documentos carregados:

{doc_context}

Posso direcionar para:
- **Relatorio estrategico** (`*relatorio`)
- **Pesquisa jurisprudencial** (`*pesquisar`)
- **Minuta de peca** (`*minutar [tipo]`)
- **Agente especifico** (use @nome-do-agente)

O que deseja?"""


async def _handle_agents_list(session_id: str) -> ChatMessage:
    content = """## Agentes Disponiveis

| Agente | Funcao | Tier |
|--------|--------|------|
| @legal-chief | Orquestrador do pipeline | Orchestrator |
| @barbosa-classifier | Classificacao TPU/SGT | Tier 0 |
| @fux-procedural | Admissibilidade e requisitos | Tier 0 |
| @cnj-compliance | Conformidade CNJ | Tier 0 |
| @mendes-researcher | Pesquisa constitucional | Tier 1 |
| @toffoli-aggregator | Consolidacao de precedentes | Tier 1 |
| @moraes-analyst | Direitos fundamentais | Tier 1 |
| @carmem-relator | Perfil do Relator | Tier 2 |
| @fachin-precedent | Analise de precedentes | Tier 2 |
| @nunes-quantitative | Jurimetria | Tier 2 |
| @barroso-strategist | Estrategia argumentativa | Tier 2 |
| @theodoro-validator | Validacao processual | Tier 3 |
| @marinoni-quality | Qualidade de precedentes | Tier 3 |
| @datajud-formatter | Formatacao DATAJUD | Tier 3 |
| @weber-indexer | Indexacao tematica | Tier 3 |

**Para acionar um agente**, mencione-o pelo @nome ou descreva sua necessidade.
**Para criar um novo agente**, use o painel de Agentes e clique em "Criar Agente via Skill"."""

    return await session_repository.add_agent_response(
        session_id=session_id,
        content=content,
        agent_id="legal-chief",
        agent_name="@legal-chief",
    )


async def _handle_clip_instructions(session_id: str) -> ChatMessage:
    content = """## Como Recortar Documentos

Use o **Painel de Documentos** (icone de documento na barra lateral) para:

1. **Selecionar paginas** - Clique na pagina desejada
2. **Recortar texto** - Selecione a area de texto
3. **Recortar imagem** - Use a ferramenta de selecao de area
4. **Rotular o recorte** - Adicione um label descritivo

Os recortes ficam disponiveis para:
- **Inserir em pecas** - Referenciados por ID e pagina
- **Citar no chat** - Use o botao de referencia
- **Incluir em relatorios** - Com remissao automatica

**Formato de remissao:** (Doc. ID XXX, fl. N)"""

    return await session_repository.add_agent_response(
        session_id=session_id,
        content=content,
        agent_id="legal-chief",
        agent_name="@legal-chief",
    )
