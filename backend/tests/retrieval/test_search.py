from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import DocFormat, Document, ProjectDocument
from app.models.project import Project
from app.models.section import Section
from app.retrieval.search import keyword_search, vector_search

DIM = 1024


def _vec(*nonzero: tuple[int, float]) -> list[float]:
    v = [0.0] * DIM
    for idx, val in nonzero:
        v[idx] = val
    return v


async def _make_project_with_document(db_session: AsyncSession, name: str) -> tuple[Project, Document, Section]:
    project = Project(name=name)
    db_session.add(project)
    await db_session.flush()

    document = Document(
        sha256=f"{name}".ljust(64, "0"),
        title=f"Doc {name}",
        format=DocFormat.txt,
        original_name="d.txt",
        storage_path="/tmp/d.txt",
        raw_text="placeholder",
    )
    db_session.add(document)
    await db_session.flush()
    db_session.add(ProjectDocument(project_id=project.id, document_id=document.id))

    section = Section(
        document_id=document.id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=11,
    )
    db_session.add(section)
    await db_session.flush()
    return project, document, section


def _make_chunk(
    document: Document,
    section: Section,
    ordinal: int,
    embedding: list[float] | None,
    text: str | None = None,
) -> Chunk:
    body = text if text is not None else f"chunk {ordinal}"
    return Chunk(
        document_id=document.id,
        section_id=section.id,
        ordinal=ordinal,
        text=body,
        embed_text=f"T\n\n{body}",
        char_start=0,
        char_end=len(body),
        token_count=len(body.split()),
        embedding=embedding,
    )


async def test_vector_search_respects_the_mandatory_project_filter(db_session: AsyncSession) -> None:
    project_a, doc_a, section_a = await _make_project_with_document(db_session, "A")
    project_b, doc_b, section_b = await _make_project_with_document(db_session, "B")

    chunk_a = _make_chunk(doc_a, section_a, 1, _vec((0, 1.0)))
    chunk_b = _make_chunk(doc_b, section_b, 1, _vec((1, 1.0)))
    db_session.add_all([chunk_a, chunk_b])
    await db_session.flush()

    # Query identical to chunk_b's embedding, but searched scoped to project A.
    # If isolation were broken, chunk_b would be the (only sensible) result.
    results = await vector_search(db_session, project_id=project_a.id, query_embedding=_vec((1, 1.0)))

    result_ids = [c.id for c, _, _ in results]
    assert chunk_b.id not in result_ids
    assert result_ids == [chunk_a.id]


async def test_vector_search_orders_nearest_first(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "C")

    query = _vec((0, 1.0))
    near = _make_chunk(document, section, 1, _vec((0, 1.0), (1, 0.1)))
    mid = _make_chunk(document, section, 2, _vec((0, 1.0), (1, 1.0)))
    far = _make_chunk(document, section, 3, _vec((1, 1.0)))
    db_session.add_all([near, mid, far])
    await db_session.flush()

    results = await vector_search(db_session, project_id=project.id, query_embedding=query)
    ordered_ids = [c.id for c, _, _ in results]
    assert ordered_ids == [near.id, mid.id, far.id]


async def test_vector_search_returns_empty_for_project_with_no_chunks(db_session: AsyncSession) -> None:
    project = Project(name="Empty")
    db_session.add(project)
    await db_session.flush()

    results = await vector_search(db_session, project_id=project.id, query_embedding=_vec((0, 1.0)))
    assert results == []


async def test_vector_search_ignores_chunks_with_no_embedding_yet(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "D")
    unembedded = Chunk(
        document_id=document.id,
        section_id=section.id,
        ordinal=1,
        text="not yet embedded",
        embed_text="T\n\nnot yet embedded",
        char_start=0,
        char_end=16,
        token_count=3,
        embedding=None,
    )
    db_session.add(unembedded)
    await db_session.flush()

    results = await vector_search(db_session, project_id=project.id, query_embedding=_vec((0, 1.0)))
    assert results == []


async def test_vector_search_respects_top_k(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "E")
    chunks = [_make_chunk(document, section, i, _vec((0, 1.0), (1, i * 0.1))) for i in range(5)]
    db_session.add_all(chunks)
    await db_session.flush()

    results = await vector_search(db_session, project_id=project.id, query_embedding=_vec((0, 1.0)), top_k=2)
    assert len(results) == 2


# --- keyword_search ----------------------------------------------------


async def test_keyword_search_respects_the_mandatory_project_filter(db_session: AsyncSession) -> None:
    project_a, doc_a, section_a = await _make_project_with_document(db_session, "F")
    project_b, doc_b, section_b = await _make_project_with_document(db_session, "G")

    chunk_a = _make_chunk(doc_a, section_a, 1, None, text="The serializable isolation level.")
    chunk_b = _make_chunk(doc_b, section_b, 1, None, text="The serializable isolation level.")
    db_session.add_all([chunk_a, chunk_b])
    await db_session.flush()

    results = await keyword_search(db_session, project_id=project_a.id, query_text="serializable isolation")

    result_ids = [c.id for c, _, _ in results]
    assert chunk_b.id not in result_ids
    assert result_ids == [chunk_a.id]


async def test_keyword_search_excludes_chunks_that_do_not_match(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "H")
    matching = _make_chunk(document, section, 1, None, text="Transactions and isolation levels.")
    non_matching = _make_chunk(document, section, 2, None, text="Unrelated content about cooking.")
    db_session.add_all([matching, non_matching])
    await db_session.flush()

    results = await keyword_search(db_session, project_id=project.id, query_text="isolation levels")

    result_ids = [c.id for c, _, _ in results]
    assert result_ids == [matching.id]


async def test_keyword_search_orders_best_match_first(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "I")
    weak = _make_chunk(document, section, 1, None, text="Isolation is mentioned once here.")
    strong = _make_chunk(
        document, section, 2, None, text="Isolation isolation isolation: the whole passage is about isolation."
    )
    db_session.add_all([weak, strong])
    await db_session.flush()

    results = await keyword_search(db_session, project_id=project.id, query_text="isolation")

    ordered_ids = [c.id for c, _, _ in results]
    assert ordered_ids == [strong.id, weak.id]


async def test_keyword_search_returns_empty_for_project_with_no_matches(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "J")
    chunk = _make_chunk(document, section, 1, None, text="Completely unrelated text.")
    db_session.add(chunk)
    await db_session.flush()

    results = await keyword_search(db_session, project_id=project.id, query_text="serializable isolation")
    assert results == []


async def test_keyword_search_respects_top_k(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "K")
    chunks = [
        _make_chunk(document, section, i, None, text=f"Isolation level number {i}.") for i in range(5)
    ]
    db_session.add_all(chunks)
    await db_session.flush()

    results = await keyword_search(db_session, project_id=project.id, query_text="isolation", top_k=2)
    assert len(results) == 2
