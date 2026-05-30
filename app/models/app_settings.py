from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AppSettings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    papierkram_api_url: Mapped[str] = mapped_column(String, nullable=False, default="")
    papierkram_api_key_encrypted: Mapped[str] = mapped_column(String, nullable=False, default="")
    paperless_base_url: Mapped[str] = mapped_column(String, nullable=False, default="")
    paperless_api_token_encrypted: Mapped[str] = mapped_column(String, nullable=False, default="")
    polling_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    default_tags: Mapped[str | None] = mapped_column(String, nullable=True)
    default_document_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    default_correspondent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sync_non_draft_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
