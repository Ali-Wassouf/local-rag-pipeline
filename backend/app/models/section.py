import enum

from sqlalchemy import BigInteger, ForeignKey, Integer, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import LtreeType


class StructureSource(str, enum.Enum):
    detected = "detected"
    manual = "manual"


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(LtreeType(), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    display_path: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[StructureSource] = mapped_column(
        SqlEnum(
            StructureSource,
            name="structure_source",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        server_default=StructureSource.detected.value,
    )
