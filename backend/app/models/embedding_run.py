from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmbeddingRun(Base):
    __tablename__ = "embedding_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
