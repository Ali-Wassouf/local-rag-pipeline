from sqlalchemy.ext.asyncio import AsyncSession

from app.models.section import Section
from app.models.summary import SectionSummary
from app.retrieval.survey import survey_search
from tests.retrieval.test_search import _make_project_with_document, _vec  # noqa: F401


async def _add_section(db_session: AsyncSession, document_id: int, ordinal: int) -> Section:
    section = Section(
        document_id=document_id,
        path=f"n{ordinal}",
        title=f"T{ordinal}",
        display_path=f"T{ordinal}",
        depth=1,
        ordinal=ordinal,
        char_start=0,
        char_end=1,
    )
    db_session.add(section)
    await db_session.flush()
    return section


def _make_summary(
    document_id: int, section_id: int, embedding: list[float] | None, text: str = "a summary"
) -> SectionSummary:
    return SectionSummary(
        section_id=section_id,
        document_id=document_id,
        summary=text,
        embedding=embedding,
        model="rag-gen",
    )


async def test_survey_search_respects_the_mandatory_project_filter(
    db_session: AsyncSession,
) -> None:
    project_a, doc_a, section_a = await _make_project_with_document(db_session, "A")
    project_b, doc_b, section_b = await _make_project_with_document(db_session, "B")

    summary_a = _make_summary(doc_a.id, section_a.id, _vec((0, 1.0)))
    summary_b = _make_summary(doc_b.id, section_b.id, _vec((1, 1.0)))
    db_session.add_all([summary_a, summary_b])
    await db_session.flush()

    results = await survey_search(
        db_session, project_id=project_a.id, query_embedding=_vec((1, 1.0))
    )

    result_ids = [s.id for s, _sec, _doc in results]
    assert summary_b.id not in result_ids
    assert result_ids == [summary_a.id]


async def test_survey_search_orders_nearest_first(db_session: AsyncSession) -> None:
    project, document, section = await _make_project_with_document(db_session, "C")
    section2 = await _add_section(db_session, document.id, ordinal=2)

    query = _vec((0, 1.0))
    near = _make_summary(document.id, section.id, _vec((0, 1.0), (1, 0.1)), "near")
    far = _make_summary(document.id, section2.id, _vec((1, 1.0)), "far")
    db_session.add_all([near, far])
    await db_session.flush()

    results = await survey_search(db_session, project_id=project.id, query_embedding=query)
    ordered_ids = [s.id for s, _sec, _doc in results]
    assert ordered_ids == [near.id, far.id]


async def test_survey_search_returns_empty_for_project_with_no_summaries(
    db_session: AsyncSession,
) -> None:
    project, _document, _section = await _make_project_with_document(db_session, "D")

    results = await survey_search(
        db_session, project_id=project.id, query_embedding=_vec((0, 1.0))
    )
    assert results == []


async def test_survey_search_respects_top_k(db_session: AsyncSession) -> None:
    project, document, first_section = await _make_project_with_document(db_session, "E")

    sections = [first_section] + [
        await _add_section(db_session, document.id, ordinal=i) for i in range(2, 6)
    ]
    summaries = [
        _make_summary(document.id, section.id, _vec((0, 1.0), (1, i * 0.1)))
        for i, section in enumerate(sections)
    ]
    db_session.add_all(summaries)
    await db_session.flush()

    results = await survey_search(
        db_session, project_id=project.id, query_embedding=_vec((0, 1.0)), top_k=2
    )
    assert len(results) == 2
