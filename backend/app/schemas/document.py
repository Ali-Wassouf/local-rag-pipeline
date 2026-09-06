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
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    job_id: int | None
    deduped: bool
