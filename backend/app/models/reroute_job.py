"""Reroute job ORM model for agent-driven reroute execution."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RerouteJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RerouteJob(Base):
    __tablename__ = "reroute_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    shipment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    status: Mapped[RerouteJobStatus] = mapped_column(
        Enum(
            RerouteJobStatus,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=RerouteJobStatus.QUEUED,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
