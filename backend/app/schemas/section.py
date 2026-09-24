from pydantic import BaseModel, ConfigDict

from app.models.section import StructureSource


class SectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    path: str
    title: str
    display_path: str
    depth: int
    ordinal: int
    char_start: int
    char_end: int
    source: StructureSource
    preview: str
    estimated_chunks: int


class SectionUpdate(BaseModel):
    title: str
