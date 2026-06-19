"""
Agent ORM model — represents a logistics/AI agent in the system.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AgentType(str, enum.Enum):
    LOGISTICS = "LOGISTICS"
    SOURCING = "SOURCING"
    RECIPIENT = "RECIPIENT"
    CORE_AI = "CORE_AI"


class AgentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    OFFLINE = "OFFLINE"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(
            AgentType,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            length=50,
        )
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(
            AgentStatus,
            values_callable=lambda enum: [member.value for member in enum],
            native_enum=False,
            length=50,
        ),
        default=AgentStatus.IDLE,
    )
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    efficiency_score: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    shipments: Mapped[list["Shipment"]] = relationship(
        "Shipment", back_populates="agent"
    )

    def __repr__(self) -> str:
        return f"<Agent {self.name} [{self.agent_type}]>"
