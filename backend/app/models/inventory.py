"""
Inventory ORM model — mirrors public.inventory in Supabase.
One inventory row belongs to exactly one of: farmer, store, or pantry.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.farmer import Farmer
    from app.models.store import Store


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Polymorphic owner — exactly one must be set (enforced by DB CHECK)
    farmer_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("farmers.id", ondelete="CASCADE"), nullable=True
    )
    store_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("stores.id", ondelete="CASCADE"), nullable=True
    )
    pantry_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), nullable=True   # pantries table added later
    )

    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="kg")
    min_threshold: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    max_capacity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_updated_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farmer: Mapped[Optional["Farmer"]] = relationship(
        "Farmer", back_populates="inventory"
    )
    store: Mapped[Optional["Store"]] = relationship(
        "Store", back_populates="inventory"
    )

    def __repr__(self) -> str:
        return f"<Inventory {self.item_name} qty={self.quantity}{self.unit}>"
