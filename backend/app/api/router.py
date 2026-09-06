from fastapi import APIRouter

from app.api import documents, jobs, projects

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
