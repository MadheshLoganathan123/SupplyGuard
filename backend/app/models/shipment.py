"""
Shipment ORM model.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

import uuid


class ShipmentStatus(str, enum.Enum):
    IN_TRANSIT = "IN-TRANSIT"
    REROUTED = "REROUTED"
    PERIMETER_DROP = "PERIMETER DROP"
    DELIVERED = "DELIVERED"
    DELAYED = "DELAYED"


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    shipment_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus), default=ShipmentStatus.IN_TRANSIT
    )
    agent_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("agents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="shipments")

    def __repr__(self) -> str:
        return f"<Shipment {self.shipment_code} [{self.status}]>"
