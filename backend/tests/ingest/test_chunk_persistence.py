from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.chunk import persist_chunks
from app.models.chunk import Chunk
from app.models.document import DocFormat, Document
from app.models.section import Section, StructureSource


async def _make_document_with_sections(db_session: AsyncSession) -> tuple[Document, list[Section]]:
    raw_text = "Chapter One\n\nBody text for chapter one.\n\nChapter Two\n\nBody text for chapter two."
    document = Document(
        sha256="d" * 64,
        title="Doc",
        format=DocFormat.txt,
        original_name="doc.txt",
        storage_path="/tmp/doc.txt",
        raw_text=raw_text,
    )
    db_session.add(document)
    await db_session.flush()

    section_a = Section(
        document_id=document.id,
        path="n1",
        title="Chapter One",
        display_path="Chapter One",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=41,
        source=StructureSource.detected,
    )
    section_b = Section(
        document_id=document.id,
        path="n2",
        title="Chapter Two",
        display_path="Chapter Two",
        depth=1,
        ordinal=2,
        char_start=41,
        char_end=len(raw_text),
        source=StructureSource.detected,
    )
    db_session.add_all([section_a, section_b])
    await db_session.flush()
    return document, [section_a, section_b]


async def test_persist_chunks_writes_rows_with_no_embedding_yet(
    db_session: AsyncSession,
) -> None:
    document, sections = await _make_document_with_sections(db_session)

    chunks = await persist_chunks(db_session, document, sections)
    await db_session.flush()

    assert len(chunks) == 2  # one chunk per short section
    for chunk in chunks:
        assert chunk.embedding is None
        assert chunk.embedding_run_id is None

    rows = (
        (await db_session.execute(select(Chunk).where(Chunk.document_id == document.id)))
        .scalars()
        .all()
    )
    assert len(rows) == 2


async def test_no_chunk_crosses_its_sections_char_range(db_session: AsyncSession) -> None:
    document, sections = await _make_document_with_sections(db_session)
    chunks = await persist_chunks(db_session, document, sections)

    by_section = {s.id: s for s in sections}
    for chunk in chunks:
        section = by_section[chunk.section_id]
        assert section.char_start <= chunk.char_start
        assert chunk.char_end <= section.char_end


async def test_chunk_embed_text_prefixes_the_breadcrumb_onto_text(
    db_session: AsyncSession,
) -> None:
    document, sections = await _make_document_with_sections(db_session)
    chunks = await persist_chunks(db_session, document, sections)

    chapter_one = sections[0]
    chapter_one_chunk = next(c for c in chunks if c.section_id == chapter_one.id)
    assert chapter_one_chunk.embed_text == f"{chapter_one.display_path}\n\n{chapter_one_chunk.text}"
    assert chapter_one_chunk.embed_text != chapter_one_chunk.text
