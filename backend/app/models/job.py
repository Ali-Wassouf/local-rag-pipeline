import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStage(str, enum.Enum):
    extract = "extract"
    structure = "structure"
    chunk = "chunk"
    embed = "embed"
    summarise = "summarise"
    done = "done"


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    # How many of the sections that qualify for summarising (docs/plan.md
    # §8 threshold) this job has summarised so far. NULL until the
    # summarise stage has determined the qualifying count at least once —
    # a document with generate_summary=False, or one that hasn't reached
    # this stage yet, never gets one. Lets the UI show real "N of M"
    # progress while a long document is still summarising, instead of
    # nothing being visible until the whole stage finishes.
    summary_done: Mapped[int | None] = mapped_column(Integer)
    summary_total: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
