from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False, index=True
    )
    oai_repository_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    admin_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    earliest_datestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deleted_record: Mapped[str | None] = mapped_column(String(32), nullable=True)
    granularity: Mapped[str | None] = mapped_column(String(64), nullable=True)

    metadata_formats: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    sets: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
