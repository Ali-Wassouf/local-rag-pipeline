from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.api.documents import _link_to_project
from app.models.document import Document, ProjectDocument
from app.models.project import Project
from app.models.section import Section
from app.models.summary import SectionSummary
from app.schemas.document import DocumentRead
from app.schemas.project import ProjectCreate, ProjectDocumentAttach, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(payload: ProjectCreate, db: DbSession) -> Project:
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(db: DbSession) -> list[Project]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: DbSession) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def rename_project(project_id: int, payload: ProjectUpdate, db: DbSession) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = payload.name
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: DbSession) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/documents", response_model=list[DocumentRead])
async def list_project_documents(project_id: int, db: DbSession) -> list[DocumentRead]:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    section_counts = (
        select(Section.document_id, func.count(Section.id).label("section_count"))
        .group_by(Section.document_id)
        .subquery()
    )
    summary_counts = (
        select(Section.document_id, func.count(SectionSummary.id).label("summary_count"))
        .join(SectionSummary, SectionSummary.section_id == Section.id)
        .group_by(Section.document_id)
        .subquery()
    )

    result = await db.execute(
        select(
            Document,
            func.coalesce(section_counts.c.section_count, 0),
            func.coalesce(summary_counts.c.summary_count, 0),
        )
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .outerjoin(section_counts, section_counts.c.document_id == Document.id)
        .outerjoin(summary_counts, summary_counts.c.document_id == Document.id)
        .where(ProjectDocument.project_id == project_id)
        .order_by(Document.created_at.desc())
    )

    return [
        DocumentRead(
            id=document.id,
            sha256=document.sha256,
            title=document.title,
            author=document.author,
            format=document.format,
            original_name=document.original_name,
            status=document.status,
            generate_summary=document.generate_summary,
            section_count=section_count,
            summary_count=summary_count,
            created_at=document.created_at,
        )
        for document, section_count, summary_count in result.all()
    ]


@router.post("/{project_id}/documents", status_code=201)
async def attach_document(
    project_id: int, payload: ProjectDocumentAttach, db: DbSession
) -> None:
    document = await db.get(Document, payload.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await _link_to_project(db, project_id, payload.document_id)
    await db.commit()


@router.delete("/{project_id}/documents/{document_id}", status_code=204)
async def detach_document(project_id: int, document_id: int, db: DbSession) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(ProjectDocument).where(
            ProjectDocument.project_id == project_id,
            ProjectDocument.document_id == document_id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Document is not attached to this project")
    await db.delete(link)
    await db.commit()
