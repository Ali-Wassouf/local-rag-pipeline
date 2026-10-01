import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.pipeline import retrieve
from app.retrieval.rerank import reranker_is_available
from tests.retrieval.test_search import _make_chunk, _make_project_with_document, _vec  # noqa: F401


async def test_retrieve_respects_project_isolation_with_reranker_disabled(
    db_session: AsyncSession,
) -> None:
    project_a, doc_a, section_a = await _make_project_with_document(db_session, "P")
    project_b, doc_b, section_b = await _make_project_with_document(db_session, "Q")

    chunk_a = _make_chunk(doc_a, section_a, 1, _vec((0, 1.0)), text="isolation levels in transactions")
    chunk_b = _make_chunk(doc_b, section_b, 1, _vec((0, 1.0)), text="isolation levels in transactions")
    db_session.add_all([chunk_a, chunk_b])
    await db_session.flush()

    results = await retrieve(
        db_session,
        project_id=project_a.id,
        query_embedding=_vec((0, 1.0)),
        query_text="isolation levels",
        use_reranker=False,
    )

    result_ids = [c.id for c, _, _ in results]
    assert chunk_b.id not in result_ids
    assert result_ids == [chunk_a.id]


async def test_retrieve_with_reranker_disabled_unions_vector_and_keyword_hits(
    db_session: AsyncSession,
) -> None:
    project, document, section = await _make_project_with_document(db_session, "R")

    # Only a vector hit (unrelated text, but the query embedding matches it)
    vector_only = _make_chunk(document, section, 1, _vec((0, 1.0)), text="completely unrelated prose")
    # Only a keyword hit (matches on text, but its embedding points elsewhere)
    keyword_only = _make_chunk(document, section, 2, _vec((5, 1.0)), text="serializable isolation level")
    db_session.add_all([vector_only, keyword_only])
    await db_session.flush()

    results = await retrieve(
        db_session,
        project_id=project.id,
        query_embedding=_vec((0, 1.0)),
        query_text="serializable isolation",
        use_reranker=False,
    )

    result_ids = {c.id for c, _, _ in results}
    assert result_ids == {vector_only.id, keyword_only.id}


async def test_retrieve_respects_top_k_with_reranker_disabled(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "S")
    chunks = [
        _make_chunk(document, section, i, _vec((0, 1.0), (1, i * 0.01)), text=f"isolation passage {i}")
        for i in range(5)
    ]
    db_session.add_all(chunks)
    await db_session.flush()

    results = await retrieve(
        db_session,
        project_id=project.id,
        query_embedding=_vec((0, 1.0)),
        query_text="isolation",
        top_k=2,
        use_reranker=False,
    )
    assert len(results) == 2


async def test_retrieve_with_reranker_enabled_still_respects_project_isolation(
    db_session: AsyncSession,
) -> None:
    if not reranker_is_available():
        pytest.skip("cross-encoder reranker model is not available (offline, first-download failed)")

    project_a, doc_a, section_a = await _make_project_with_document(db_session, "T")
    project_b, doc_b, section_b = await _make_project_with_document(db_session, "U")

    chunk_a = _make_chunk(doc_a, section_a, 1, _vec((0, 1.0)), text="serializable isolation level")
    chunk_b = _make_chunk(doc_b, section_b, 1, _vec((0, 1.0)), text="serializable isolation level")
    db_session.add_all([chunk_a, chunk_b])
    await db_session.flush()

    results = await retrieve(
        db_session,
        project_id=project_a.id,
        query_embedding=_vec((0, 1.0)),
        query_text="serializable isolation",
        use_reranker=True,
    )

    result_ids = [c.id for c, _, _ in results]
    assert chunk_b.id not in result_ids
    assert result_ids == [chunk_a.id]
