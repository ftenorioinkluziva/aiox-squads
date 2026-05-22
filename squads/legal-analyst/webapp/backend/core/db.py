"""Async database setup for persistent pipeline state."""
from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    split = urlsplit(url)
    query = []
    ssl_required = False
    for key, value in parse_qsl(split.query, keep_blank_values=True):
        if key == "sslmode":
            ssl_required = value == "require"
            continue
        if key == "channel_binding":
            continue
        query.append((key, value))
    if ssl_required and not any(key == "ssl" for key, _ in query):
        query.append(("ssl", "true"))
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None

if DATABASE_URL:
    engine = create_async_engine(_normalize_database_url(DATABASE_URL), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def require_database() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL nao configurada")


async def init_db() -> None:
    if engine is None:
        return
    # Import models so SQLAlchemy registers tables before create_all.
    from . import app_db  # noqa: F401
    from . import pipeline_db  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    require_database()
    assert SessionLocal is not None
    async with SessionLocal() as session:
        yield session
