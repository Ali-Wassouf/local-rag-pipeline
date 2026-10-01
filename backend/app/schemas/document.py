from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocFormat, DocStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sha256: str
    title: str
    author: str | None
    format: DocFormat
    original_name: str
    status: DocStatus
    generate_summary: bool
    # Default 0 — only populated with real counts by endpoints that join
    # for them (currently GET /projects/{id}/documents). A document with
    # generate_summary=True can still show summary_count=0 when none of its
    # sections exceeded the summarization threshold (docs/plan.md §8) —
    # these counts are what let the UI tell that apart from "has real
    # summaries" instead of looking identical.
    section_count: int = 0
    summary_count: int = 0
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    job_id: int | None
    deduped: bool
