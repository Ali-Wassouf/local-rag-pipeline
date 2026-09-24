from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocFormat, Document
from app.models.section import Section, StructureSource


async def _make_document_with_section(db_session: AsyncSession) -> tuple[Document, Section]:
    document = Document(
        sha256="b" * 64,
        title="Doc",
        format=DocFormat.txt,
        original_name="doc.txt",
        storage_path="/tmp/doc.txt",
        raw_text="Chapter One\n\nBody text.",
    )
    db_session.add(document)
    await db_session.flush()

    section = Section(
        document_id=document.id,
        path="n1",
        title="Chapter One",
        display_path="Chapter One",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=23,
        source=StructureSource.detected,
    )
    db_session.add(section)
    await db_session.flush()
    return document, section


async def test_list_sections_for_document(client: AsyncClient, db_session: AsyncSession) -> None:
    document, section = await _make_document_with_section(db_session)

    response = await client.get(f"/documents/{document.id}/sections")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == section.id
    assert body[0]["title"] == "Chapter One"
    assert body[0]["source"] == "detected"


async def test_list_sections_includes_preview_text(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    document, _section = await _make_document_with_section(db_session)

    response = await client.get(f"/documents/{document.id}/sections")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["preview"] == "Chapter One\n\nBody text."


async def test_list_sections_includes_chunk_estimate(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    document, _section = await _make_document_with_section(db_session)

    response = await client.get(f"/documents/{document.id}/sections")
    assert response.status_code == 200
    body = response.json()
    assert body[0]["estimated_chunks"] == 1


async def test_list_sections_for_unknown_document_404s(client: AsyncClient) -> None:
    response = await client.get("/documents/999999/sections")
    assert response.status_code == 404


async def test_list_sections_empty_for_document_without_sections(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    document = Document(
        sha256="c" * 64,
        title="No sections yet",
        format=DocFormat.txt,
        original_name="doc2.txt",
        storage_path="/tmp/doc2.txt",
    )
    db_session.add(document)
    await db_session.flush()

    response = await client.get(f"/documents/{document.id}/sections")
    assert response.status_code == 200
    assert response.json() == []


async def test_patch_section_title_persists_and_marks_manual(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _document, section = await _make_document_with_section(db_session)

    response = await client.patch(f"/sections/{section.id}", json={"title": "Renamed Chapter"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed Chapter"
    assert body["source"] == "manual"


async def test_patch_section_does_not_change_offsets(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _document, section = await _make_document_with_section(db_session)
    original_start, original_end = section.char_start, section.char_end

    response = await client.patch(f"/sections/{section.id}", json={"title": "New Title"})
    assert response.status_code == 200
    body = response.json()
    assert body["char_start"] == original_start
    assert body["char_end"] == original_end


async def test_patch_unknown_section_404s(client: AsyncClient) -> None:
    response = await client.patch("/sections/999999", json={"title": "x"})
    assert response.status_code == 404


async def test_patch_with_identical_title_does_not_mark_manual(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _document, section = await _make_document_with_section(db_session)

    response = await client.patch(f"/sections/{section.id}", json={"title": "Chapter One"})
    assert response.status_code == 200
    assert response.json()["source"] == "detected"


async def test_patch_with_different_title_marks_manual(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _document, section = await _make_document_with_section(db_session)

    response = await client.patch(f"/sections/{section.id}", json={"title": "New Title"})
    assert response.status_code == 200
    assert response.json()["source"] == "manual"
