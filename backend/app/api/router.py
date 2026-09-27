from fastapi import APIRouter

from app.api import conversations, documents, jobs, projects, sections

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(jobs.router)
api_router.include_router(sections.router)
api_router.include_router(conversations.router)
