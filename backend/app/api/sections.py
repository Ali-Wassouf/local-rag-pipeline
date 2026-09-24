from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.ingest.review import PREVIEW_MAX_CHARS, estimate_chunks, section_preview
from app.models.document import Document
from app.models.section import Section, StructureSource
from app.schemas.section import SectionRead, SectionUpdate

router = APIRouter(tags=["sections"])


def _to_read_model(section: Section, raw_text: str) -> SectionRead:
    section_text = raw_text[section.char_start : section.char_end]
    return SectionRead(
        id=section.id,
        document_id=section.document_id,
        path=section.path,
        title=section.title,
        display_path=section.display_path,
        depth=section.depth,
        ordinal=section.ordinal,
        char_start=section.char_start,
        char_end=section.char_end,
        source=section.source,
        preview=section_preview(raw_text, section, PREVIEW_MAX_CHARS),
        estimated_chunks=estimate_chunks(section_text),
    )


@router.get("/documents/{document_id}/sections", response_model=list[SectionRead])
async def list_sections(document_id: int, db: DbSession) -> list[SectionRead]:
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    result = await db.execute(
        select(Section).where(Section.document_id == document_id).order_by(Section.id)
    )
    raw_text = document.raw_text or ""
    return [_to_read_model(section, raw_text) for section in result.scalars().all()]


@router.patch("/sections/{section_id}", response_model=SectionRead)
async def update_section(section_id: int, payload: SectionUpdate, db: DbSession) -> SectionRead:
    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")

    if payload.title != section.title:
        section.title = payload.title
        section.source = StructureSource.manual
    await db.commit()
    await db.refresh(section)

    document = await db.get(Document, section.document_id)
    raw_text = (document.raw_text or "") if document is not None else ""
    return _to_read_model(section, raw_text)
