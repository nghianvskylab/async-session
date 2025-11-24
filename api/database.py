import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Annotated, AsyncContextManager, ParamSpec, TypeVar

from api.core.log import get_logger
from api.settings import settings
from fastapi import Depends
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

logger = get_logger("database")

connection_url = URL.create(
    "postgresql+asyncpg",
    username=settings.database.user,
    host=settings.database.host,
    port=settings.database.port,
    database=settings.database.name,
    password=settings.database.password.get_secret_value()
    if settings.database.password
    else None,
)

logger.info(f"Database connection URL: {connection_url}")

db_engine = create_async_engine(
    connection_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_timeout=5,
)

session_context = ContextVar[AsyncSession | None]("session", default=None)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    error: Exception | None = None
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        try:
            session_context.set(session)
            yield session
        except Exception as e:
            error = e
        finally:
            session_context.set(None)

    if error is not None:
        raise error


async def _get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session


NewSession = Annotated[AsyncSession, Depends(_get_session)]

Param = ParamSpec("Param")
RT = TypeVar("RT")


def ensure_session_exit(
    *, session: AsyncSession
) -> Callable[[Callable[Param, Awaitable[RT]]], Callable[Param, Awaitable[RT]]]:
    def _ensure_session_exit(
        func: Callable[Param, Awaitable[RT]]
    ) -> Callable[Param, Awaitable[RT]]:
        @wraps(func)
        async def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RT:
            try:
                return await func(*args, **kwargs)
            finally:
                try:
                    await session.__aexit__(None, None, None)
                finally:
                    pass

        return wrapper

    return _ensure_session_exit


async def bulk_session_request(
    func: Callable[[AsyncSession, int], Awaitable[RT]],
    range_: int,
) -> Sequence[RT]:
    sessions: Sequence[AsyncContextManager[AsyncSession]] = [
        get_session() for _ in range(range_)
    ]

    async def _run(
        session_ctx: AsyncContextManager[AsyncSession],
        index: int,
    ) -> RT:
        async with session_ctx as session:
            model = await func(session, index)
            return model

    results: Sequence[RT] = await asyncio.gather(
        *[_run(session_ctx, i) for i, session_ctx in enumerate(sessions)]
    )

    return results

