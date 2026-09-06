"""Test fixtures.

Runs against a real Postgres (the docker-compose `db` service) — a dedicated
`rag_test` database, recreated fresh at the start of the session and migrated
with the real Alembic revisions. No mocking of the database: pgvector and
ltree behaviour is part of what's under test.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

# Must run before any app module is imported: app.db.session builds its
# engine from settings at import time, and Settings reads this env var.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://rag:rag@localhost:5432/rag_test"

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.api.deps import get_db  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DB_NAME = "rag_test"
ADMIN_DATABASE_DSN = "postgresql://rag:rag@localhost:5432/rag"


@pytest.fixture(scope="session", autouse=True)
def _fresh_test_database() -> None:
    import asyncio

    async def _recreate() -> None:
        conn = await asyncpg.connect(ADMIN_DATABASE_DSN)
        try:
            await conn.execute(
                f"""
                SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()
                """
            )
            await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
        finally:
            await conn.close()

    asyncio.run(_recreate())

    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def db_session(_fresh_test_database: None) -> AsyncIterator[AsyncSession]:
    """A session bound to a connection whose outer transaction is rolled
    back after the test, so tests don't see each other's writes.

    The engine is created fresh per test (function-scoped): asyncpg's
    connection pool is bound to the event loop it was created on, and
    pytest-asyncio gives each test function its own loop.
    """
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conn:
        trans = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_maker() as session:
            yield session
        await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
