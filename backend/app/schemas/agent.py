"""
Pydantic schemas for Agent.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.agent import AgentStatus, AgentType


class AgentBase(BaseModel):
    name: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    sector: Optional[str] = None
    efficiency_score: float = 0.0


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    status: Optional[AgentStatus] = None
    sector: Optional[str] = None
    efficiency_score: Optional[float] = None


class AgentRead(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
