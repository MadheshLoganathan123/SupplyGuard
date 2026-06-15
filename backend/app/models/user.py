"""
User ORM model — mirrors public.users in Supabase.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.farmer import Farmer
    from app.models.driver import Driver
    from app.models.store import Store


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    auth_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="viewer")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farmers: Mapped[list["Farmer"]] = relationship("Farmer", back_populates="user")
    drivers: Mapped[list["Driver"]] = relationship("Driver", back_populates="user")
    stores:  Mapped[list["Store"]]  = relationship("Store",  back_populates="manager")

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"
