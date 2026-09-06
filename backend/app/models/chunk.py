from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 1024


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embed_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    embedding_run_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("embedding_runs.id")
    )
    tsv: Mapped[str | None] = mapped_column(TSVECTOR)
