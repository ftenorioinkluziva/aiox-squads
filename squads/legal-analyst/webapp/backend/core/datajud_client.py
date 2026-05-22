"""Client for CNJ DataJud public API."""
from __future__ import annotations

import re
from typing import Any

import httpx

from .config import DATAJUD_API_KEY, DATAJUD_BASE_URL


class DataJudConfigurationError(RuntimeError):
    pass


TRIBUNAL_ALIASES = {
    "tst": "api_publica_tst",
    "tse": "api_publica_tse",
    "stj": "api_publica_stj",
    "stm": "api_publica_stm",
    "tjdft": "api_publica_tjdft",
    "tjdf": "api_publica_tjdft",
    "tjacc": "api_publica_tjac",
    "tjac": "api_publica_tjac",
    "tjal": "api_publica_tjal",
    "tjam": "api_publica_tjam",
    "tjap": "api_publica_tjap",
    "tjba": "api_publica_tjba",
    "tjce": "api_publica_tjce",
    "tjes": "api_publica_tjes",
    "tjgo": "api_publica_tjgo",
    "tjma": "api_publica_tjma",
    "tjmg": "api_publica_tjmg",
    "tjms": "api_publica_tjms",
    "tjmt": "api_publica_tjmt",
    "tjpa": "api_publica_tjpa",
    "tjpb": "api_publica_tjpb",
    "tjpe": "api_publica_tjpe",
    "tjpi": "api_publica_tjpi",
    "tjpr": "api_publica_tjpr",
    "tjrj": "api_publica_tjrj",
    "tjrn": "api_publica_tjrn",
    "tjro": "api_publica_tjro",
    "tjrr": "api_publica_tjrr",
    "tjrs": "api_publica_tjrs",
    "tjsc": "api_publica_tjsc",
    "tjse": "api_publica_tjse",
    "tjsp": "api_publica_tjsp",
    "tjto": "api_publica_tjto",
    "trf1": "api_publica_trf1",
    "trf2": "api_publica_trf2",
    "trf3": "api_publica_trf3",
    "trf4": "api_publica_trf4",
    "trf5": "api_publica_trf5",
    "trf6": "api_publica_trf6",
    "tjmmg": "api_publica_tjmmg",
    "tjmrs": "api_publica_tjmrs",
    "tjmsp": "api_publica_tjmsp",
}

for number in range(1, 25):
    TRIBUNAL_ALIASES[f"trt{number}"] = f"api_publica_trt{number}"

for uf in (
    "ac", "al", "am", "ap", "ba", "ce", "dft", "es", "go", "ma", "mg", "ms", "mt",
    "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to",
):
    TRIBUNAL_ALIASES[f"tre-{uf}"] = f"api_publica_tre-{uf}"
    TRIBUNAL_ALIASES[f"tre{uf}"] = f"api_publica_tre-{uf}"


def normalize_process_number(value: str) -> str:
    return re.sub(r"\D", "", value)


def resolve_tribunal_alias(tribunal_alias: str) -> str:
    clean = tribunal_alias.strip().lower().replace("_search", "")
    if clean.startswith("api_publica_"):
        return clean
    if clean in TRIBUNAL_ALIASES:
        return TRIBUNAL_ALIASES[clean]
    raise ValueError(f"Alias de tribunal nao suportado: {tribunal_alias}")


def _headers() -> dict[str, str]:
    if not DATAJUD_API_KEY:
        raise DataJudConfigurationError("DATAJUD_API_KEY nao configurada")
    token = DATAJUD_API_KEY.strip()
    authorization = token if token.lower().startswith("apikey ") else f"APIKey {token}"
    return {
        "Authorization": authorization,
        "Content-Type": "application/json",
    }


async def search_datajud(tribunal_alias: str, query: dict[str, Any], size: int | None = None) -> dict[str, Any]:
    index = resolve_tribunal_alias(tribunal_alias)
    payload: dict[str, Any] = {"query": query}
    if size is not None:
        payload["size"] = size
    url = f"{DATAJUD_BASE_URL.rstrip('/')}/{index}/_search"
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, headers=_headers(), json=payload)
    response.raise_for_status()
    return response.json()


async def search_process_number(tribunal_alias: str, process_number: str) -> dict[str, Any]:
    number = normalize_process_number(process_number)
    if not number:
        raise ValueError("Numero do processo vazio")
    return await search_datajud(
        tribunal_alias=tribunal_alias,
        query={"match": {"numeroProcesso": number}},
        size=1,
    )
