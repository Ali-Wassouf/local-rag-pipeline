import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocFormat, Document, ProjectDocument
from app.models.project import Project
from app.models.section import Section
from app.retrieval.rerank import reranker_is_available, rerank
from tests.retrieval.test_search import _make_chunk, _make_project_with_document  # noqa: F401


async def _seeded_candidate(
    db_session: AsyncSession, name: str, text: str
) -> tuple:
    project, document, section = await _make_project_with_document(db_session, name)
    chunk = _make_chunk(document, section, 1, None, text=text)
    db_session.add(chunk)
    await db_session.flush()
    return chunk, section, document


async def test_rerank_returns_empty_for_no_candidates() -> None:
    assert await rerank("anything", []) == []


async def test_rerank_puts_the_more_relevant_candidate_first(db_session: AsyncSession) -> None:
    if not reranker_is_available():
        pytest.skip("cross-encoder reranker model is not available (offline, first-download failed)")

    relevant = await _seeded_candidate(
        db_session, "L", "Serializable isolation is the strongest transaction isolation level."
    )
    irrelevant = await _seeded_candidate(
        db_session, "M", "The recipe calls for two cups of flour and a pinch of salt."
    )

    results = await rerank("What is serializable isolation?", [irrelevant, relevant])

    assert results[0][0].id == relevant[0].id


async def test_rerank_respects_top_k(db_session: AsyncSession) -> None:
    if not reranker_is_available():
        pytest.skip("cross-encoder reranker model is not available (offline, first-download failed)")

    candidates = [
        await _seeded_candidate(db_session, f"N{i}", f"Isolation level passage number {i}.")
        for i in range(5)
    ]

    results = await rerank("isolation level", candidates, top_k=2)
    assert len(results) == 2
