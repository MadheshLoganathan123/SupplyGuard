from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AgentLogRead(BaseModel):
    id: str
    agent_name: str
    agent_type: str
    action_type: str
    status: str
    message: Optional[str] = None
    payload: Optional[Any] = None
    result: Optional[Any] = None
    confidence: Optional[float] = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentLogCreate(BaseModel):
    agent_name: str
    agent_type: str = "logistics"
    action_type: str
    delivery_id: Optional[str] = None
    threat_id: Optional[str] = None
    route_id: Optional[str] = None
    farmer_id: Optional[str] = None
    payload: Optional[Any] = None
    result: Optional[Any] = None
    confidence: Optional[float] = None
    status: str = "success"
    message: Optional[str] = None

