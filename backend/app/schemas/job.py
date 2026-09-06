from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    stage: str
    progress: float
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
