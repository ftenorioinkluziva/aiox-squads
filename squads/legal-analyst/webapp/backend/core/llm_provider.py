"""LLM provider abstraction with Anthropic primary and OpenAI fallback."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import anthropic
from openai import OpenAI

from .config import (
    AGENTS_DIR,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)

_anthropic_client: anthropic.Anthropic | None = None
_openai_client: OpenAI | None = None


class LLMConfigurationError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str


def load_agent_prompt(agent_id: str) -> str:
    agent_file = AGENTS_DIR / f"{agent_id}.md"
    if agent_file.exists():
        return agent_file.read_text(encoding="utf-8")
    return ""


def build_legal_system_prompt(
    agent_id: str,
    doc_context: str = "",
    ref_context: str = "",
    considerations: str = "",
    extra_context: str = "",
) -> str:
    agent_prompt = load_agent_prompt(agent_id)
    system_parts = [
        "Voce e um agente do Legal Analyst Squad - sistema de analise juridica processual.",
        "Responda em portugues brasileiro. Seja preciso, fundamentado e estruturado.",
        "",
        "## Principios Imutaveis",
        "- JURISPRUDENCIA > OPINIAO: Toda analise fundamentada em julgados reais",
        "- CPC Art. 489 par. 1o: Fundamentacao qualificada obrigatoria",
        "- CNJ-COMPLIANT: Resolucoes do CNJ sao gates obrigatorios",
        "- PRECEDENTE E LEI: Sistema de precedentes do CPC (Art. 926-928)",
    ]

    if agent_prompt:
        system_parts.extend(["", "## Definicao do Agente", agent_prompt])
    if doc_context:
        system_parts.extend(["", "## Documentos Carregados", doc_context])
    if ref_context:
        system_parts.extend(["", "## Recortes Referenciados", ref_context])
    if considerations:
        system_parts.extend(["", "## Consideracoes do Advogado", considerations])
    if extra_context:
        system_parts.extend(["", "## Contexto da Execucao", extra_context])

    return "\n".join(system_parts)


def _get_anthropic_client() -> anthropic.Anthropic | None:
    global _anthropic_client
    if _anthropic_client is None and ANTHROPIC_API_KEY:
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_openai_client() -> OpenAI | None:
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _call_anthropic_sync(system_prompt: str, messages: list[dict[str, str]]) -> str:
    client = _get_anthropic_client()
    if client is None:
        raise LLMConfigurationError("ANTHROPIC_API_KEY nao configurada")
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def _call_openai_sync(system_prompt: str, messages: list[dict[str, str]]) -> str:
    client = _get_openai_client()
    if client is None:
        raise LLMConfigurationError("OPENAI_API_KEY nao configurada")
    chat_messages = [{"role": "system", "content": system_prompt}, *messages]
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=chat_messages,
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return content or ""


async def generate_text(system_prompt: str, messages: list[dict[str, str]]) -> LLMResult:
    if ANTHROPIC_API_KEY:
        try:
            text = await asyncio.to_thread(_call_anthropic_sync, system_prompt, messages)
            return LLMResult(text=text, provider="anthropic", model=ANTHROPIC_MODEL)
        except Exception as exc:
            if not OPENAI_API_KEY:
                raise
            logger.warning("Anthropic failed; trying OpenAI fallback: %s", exc)

    if OPENAI_API_KEY:
        text = await asyncio.to_thread(_call_openai_sync, system_prompt, messages)
        return LLMResult(text=text, provider="openai", model=OPENAI_MODEL)

    raise LLMConfigurationError(
        "Nenhum provedor LLM configurado. Defina ANTHROPIC_API_KEY ou OPENAI_API_KEY."
    )
