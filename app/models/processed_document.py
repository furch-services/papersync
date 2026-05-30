from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProcessedDocument(Base):
    __tablename__ = "processed_documents"
    __table_args__ = (Index("idx_processed_papierkram_id", "papierkram_document_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    papierkram_document_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    paperless_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paperless_task_uuid: Mapped[str | None] = mapped_column(String, nullable=True)
    invoice_no: Mapped[str | None] = mapped_column(String, nullable=True)
    document_date: Mapped[str | None] = mapped_column(String, nullable=True)
    total_gross: Mapped[float | None] = mapped_column(Float, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
