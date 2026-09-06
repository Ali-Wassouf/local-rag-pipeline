from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.chunk import EMBEDDING_DIM


class SectionSummary(Base):
    __tablename__ = "section_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
