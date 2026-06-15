"""
Driver ORM model — mirrors public.drivers in Supabase.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="motorcycle"
    )
    vehicle_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    capacity_kg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2), nullable=True
    )
    sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle")
    current_lat: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6), nullable=True
    )
    current_lng: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 6), nullable=True
    )
    utilization_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )
    agent_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="drivers")

    def __repr__(self) -> str:
        return f"<Driver {self.id} [{self.vehicle_type} / {self.status}]>"
