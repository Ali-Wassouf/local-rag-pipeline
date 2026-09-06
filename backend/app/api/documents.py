import hashlib
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Form, HTTPException, UploadFile
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.config import get_settings
from app.models.document import DocFormat, Document, ProjectDocument
from app.models.job import IngestJob, JobStage
from app.models.project import Project
from app.schemas.document import DocumentRead, DocumentUploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

_EXTENSION_FORMATS: dict[str, DocFormat] = {
    ".pdf": DocFormat.pdf,
    ".docx": DocFormat.docx,
    ".pptx": DocFormat.pptx,
    ".txt": DocFormat.txt,
    ".md": DocFormat.md,
}


def _format_from_filename(filename: str) -> DocFormat:
    suffix = Path(filename).suffix.lower()
    doc_format = _EXTENSION_FORMATS.get(suffix)
    if doc_format is None:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {suffix or filename}"
        )
    return doc_format


async def _link_to_project(db: DbSession, project_id: int, document_id: int) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    existing = await db.execute(
        select(ProjectDocument).where(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(ProjectDocument(project_id=project_id, document_id=document_id))


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    db: DbSession,
    file: UploadFile,
    title: str | None = Form(None),
    author: str | None = Form(None),
    project_id: int | None = Form(None),
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    doc_format = _format_from_filename(file.filename)

    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()

    existing = await db.execute(select(Document).where(Document.sha256 == sha256))
    document = existing.scalar_one_or_none()

    if document is not None:
        if project_id is not None:
            await _link_to_project(db, project_id, document.id)
            await db.commit()
        return DocumentUploadResponse(
            document=DocumentRead.model_validate(document), job_id=None, deduped=True
        )

    settings = get_settings()
    storage_path = settings.storage_dir / f"{sha256}{Path(file.filename).suffix.lower()}"
    async with aiofiles.open(storage_path, "wb") as out:
        await out.write(content)

    document = Document(
        sha256=sha256,
        title=title or Path(file.filename).stem,
        author=author,
        format=doc_format,
        original_name=file.filename,
        storage_path=str(storage_path),
    )
    db.add(document)
    await db.flush()

    job = IngestJob(document_id=document.id, stage=JobStage.extract.value, progress=0.0)
    db.add(job)

    if project_id is not None:
        await _link_to_project(db, project_id, document.id)

    await db.commit()
    await db.refresh(document)
    await db.refresh(job)

    return DocumentUploadResponse(
        document=DocumentRead.model_validate(document), job_id=job.id, deduped=False
    )


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: int, db: DbSession) -> Document:
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
