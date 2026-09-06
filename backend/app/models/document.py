import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DocFormat(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"
    pptx = "pptx"
    txt = "txt"
    md = "md"


class DocStatus(str, enum.Enum):
    uploaded = "uploaded"
    extracting = "extracting"
    awaiting_review = "awaiting_review"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sha256: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(Text)
    format: Mapped[DocFormat] = mapped_column(
        SqlEnum(DocFormat, name="doc_format", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DocStatus] = mapped_column(
        SqlEnum(DocStatus, name="doc_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        server_default=DocStatus.uploaded.value,
    )
    page_offset: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
