from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead

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


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: DbSession) -> None:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
