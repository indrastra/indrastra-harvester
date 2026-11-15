from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class HarvestJob(Base):
    __tablename__ = "harvest_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", nullable=False, index=True)
    metadata_prefix: Mapped[str] = mapped_column(String(128), nullable=False)
    set_spec: Mapped[str | None] = mapped_column(String(255))
    from_date: Mapped[str | None] = mapped_column(String(64))
    until_date: Mapped[str | None] = mapped_column(String(64))
    resumption_token: Mapped[str | None] = mapped_column(Text)
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class HarvestJobLog(Base):
    __tablename__ = "harvest_job_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("harvest_jobs.id", ondelete="CASCADE"), index=True)
    level: Mapped[str] = mapped_column(String(16), default="INFO", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class SourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint("repository_id", "oai_identifier", name="uq_source_record_repository_identifier"),
        Index("ix_source_records_datestamp", "repository_id", "datestamp"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False)
    oai_identifier: Mapped[str] = mapped_column(String(1024), nullable=False)
    datestamp: Mapped[str | None] = mapped_column(String(64))
    set_specs: Mapped[str | None] = mapped_column(Text)
    metadata_prefix: Mapped[str] = mapped_column(String(128), nullable=False)
    original_xml: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    source_status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    first_harvested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_harvested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
