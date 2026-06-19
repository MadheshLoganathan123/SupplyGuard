"""
Agent log ORM model — stores immutable AI negotiation actions and decisions.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AgentLogStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="logistics")
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    delivery_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    threat_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    route_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    farmer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    status: Mapped[AgentLogStatus] = mapped_column(
        Enum(
            AgentLogStatus,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=AgentLogStatus.SUCCESS,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
