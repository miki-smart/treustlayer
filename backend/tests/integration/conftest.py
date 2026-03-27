"""
Integration test conftest — uses PostgreSQL-dialect SQLite workaround.

SQLite does not support named schemas. We use SQLAlchemy's
`schema_translate_map` to map all schema names to None so that
create_all() flattens them into one namespace. Integration tests
verify API-level behavior; the schema isolation is a deployment concern.
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event as sa_event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.db.base import Base
from app.main import app
from app.core.database import get_async_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# All PostgreSQL schemas that models declare — mapped to None for SQLite
_SCHEMA_MAP = {
    "identity": None,
    "kyc": None,
    "consent": None,
    "auth": None,
    "app_registry": None,
    "session": None,
    "event_store": None,
    "webhook": None,
}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def integration_db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        execution_options={"schema_translate_map": _SCHEMA_MAP},
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn.execution_options(schema_translate_map=_SCHEMA_MAP)
            )
        )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        sync_session_class=None,
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.drop_all(
                sync_conn.execution_options(schema_translate_map=_SCHEMA_MAP)
            )
        )
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def integration_client(
    integration_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client wired to the in-memory SQLite integration DB."""
    async def override_session():
        yield integration_db_session

    app.dependency_overrides[get_async_session] = override_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
