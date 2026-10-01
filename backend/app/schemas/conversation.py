from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str | None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str
    mode: Literal["lookup", "survey"] = "lookup"


class CitationRead(BaseModel):
    # Exactly one of chunk_id / is_summary=True with no chunk is possible —
    # a lookup citation points at a passage, a survey citation at a
    # section's summary (CLAUDE.md invariant 6: never render the latter as
    # a passage the model read).
    chunk_id: int | None = None
    rank: int
    document_title: str
    display_path: str
    is_summary: bool = False


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    citations: list[CitationRead]
