from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.models.job import IngestJob
from app.schemas.job import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: int, db: DbSession) -> IngestJob:
    job = await db.get(IngestJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
