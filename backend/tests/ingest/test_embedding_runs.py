from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.embed import get_or_create_embedding_run
from app.models.embedding_run import EmbeddingRun


async def test_first_call_creates_a_new_current_run(db_session: AsyncSession) -> None:
    run = await get_or_create_embedding_run(db_session, model="qwen3-embedding:0.6b", dimension=1024)
    await db_session.flush()

    assert run.model == "qwen3-embedding:0.6b"
    assert run.dimension == 1024
    assert run.is_current is True


async def test_second_call_for_same_model_returns_the_same_row(db_session: AsyncSession) -> None:
    first = await get_or_create_embedding_run(db_session, model="qwen3-embedding:0.6b", dimension=1024)
    await db_session.flush()

    second = await get_or_create_embedding_run(db_session, model="qwen3-embedding:0.6b", dimension=1024)
    await db_session.flush()

    assert second.id == first.id

    rows = (
        (
            await db_session.execute(
                select(EmbeddingRun).where(EmbeddingRun.model == "qwen3-embedding:0.6b")
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1


async def test_different_model_creates_a_separate_run(db_session: AsyncSession) -> None:
    first = await get_or_create_embedding_run(db_session, model="model-a", dimension=1024)
    second = await get_or_create_embedding_run(db_session, model="model-b", dimension=768)
    await db_session.flush()

    assert first.id != second.id
    assert second.dimension == 768
