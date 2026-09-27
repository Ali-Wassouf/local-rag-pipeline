from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str | None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str


class CitationRead(BaseModel):
    chunk_id: int
    rank: int
    document_title: str
    display_path: str


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    citations: list[CitationRead]
