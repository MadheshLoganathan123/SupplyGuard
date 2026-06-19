"""
Telemetry ORM model — stores recent node and shipment telemetry for dashboard consumption.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TelemetryMessage(Base):
    __tablename__ = "telemetry"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    node_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
