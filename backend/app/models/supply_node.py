"""
Supply node ORM model — unified topology nodes for the Network screen.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NodeType(str, enum.Enum):
    FARM = "FARM"
    WAREHOUSE = "WAREHOUSE"
    RETAIL = "RETAIL"
    SHIPPING = "SHIPPING"


class NodeStatus(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    AT_RISK = "AT_RISK"
    BLOCKED = "BLOCKED"
    INACTIVE = "INACTIVE"


class SupplyNode(Base):
    __tablename__ = "supply_nodes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=NodeStatus.OPERATIONAL.value)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    inventory_level: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    inventory_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    threat_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    throughput: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    connections: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
