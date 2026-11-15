from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class NormalizedRecord(Base):
    __tablename__ = "normalized_records"
    __table_args__ = (
        UniqueConstraint("source_record_id", name="uq_normalized_source_record"),
        Index("ix_normalized_records_repository", "repository_id"),
        Index("ix_normalized_records_deleted", "is_deleted"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_record_id: Mapped[int] = mapped_column(
        ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False
    )
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False
    )
    oai_identifier: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_prefix: Mapped[str] = mapped_column(String(128), nullable=False)
    schema: Mapped[str] = mapped_column(String(128), nullable=False)
    normalization_version: Mapped[str] = mapped_column(String(32), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    title: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    creators: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    subjects: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    publication_date: Mapped[str | None] = mapped_column(String(64))
    resource_type: Mapped[str | None] = mapped_column(String(255))
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    normalized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
