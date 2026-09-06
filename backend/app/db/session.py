from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

engine: AsyncEngine = create_async_engine(_settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
