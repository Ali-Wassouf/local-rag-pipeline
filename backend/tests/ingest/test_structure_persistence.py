from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.structure import SectionDraft, StructureResult, persist_structure
from app.models.document import DocFormat, Document
from app.models.section import Section


async def _make_document(db_session: AsyncSession) -> Document:
    document = Document(
        sha256="a" * 64,
        title="Test Doc",
        format=DocFormat.txt,
        original_name="test.txt",
        storage_path="/tmp/test.txt",
    )
    db_session.add(document)
    await db_session.flush()
    return document


async def test_persist_structure_writes_sections_and_raw_text(
    db_session: AsyncSession,
) -> None:
    document = await _make_document(db_session)
    raw_text = "Chapter One\n\nBody text for chapter one."
    result = StructureResult(
        raw_text=raw_text,
        sections=[
            SectionDraft(
                path="n1",
                title="Chapter One",
                display_path="Chapter One",
                depth=1,
                ordinal=1,
                char_start=0,
                char_end=len(raw_text),
            )
        ],
    )

    sections = await persist_structure(db_session, document, result)
    await db_session.flush()

    assert document.raw_text == raw_text
    assert len(sections) == 1

    rows = (
        (await db_session.execute(select(Section).where(Section.document_id == document.id)))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.path == "n1"
    assert row.title == "Chapter One"
    assert row.display_path == "Chapter One"
    assert row.depth == 1
    assert row.ordinal == 1
    assert row.char_start == 0
    assert row.char_end == len(raw_text)
    assert row.source.value == "detected"


async def test_persist_structure_writes_nested_paths(db_session: AsyncSession) -> None:
    document = await _make_document(db_session)
    result = StructureResult(
        raw_text="Chapter One\n\nSection 1.1",
        sections=[
            SectionDraft(
                path="n1",
                title="Chapter One",
                display_path="Chapter One",
                depth=1,
                ordinal=1,
                char_start=0,
                char_end=11,
            ),
            SectionDraft(
                path="n1.n1",
                title="Section 1.1",
                display_path="Chapter One > Section 1.1",
                depth=2,
                ordinal=1,
                char_start=13,
                char_end=24,
            ),
        ],
    )

    await persist_structure(db_session, document, result)
    await db_session.flush()

    rows = (
        (
            await db_session.execute(
                select(Section)
                .where(Section.document_id == document.id)
                .order_by(Section.ordinal)
            )
        )
        .scalars()
        .all()
    )
    assert [r.path for r in rows] == ["n1", "n1.n1"]
