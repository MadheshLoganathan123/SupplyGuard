from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DashboardMetrics(BaseModel):
    threatLevel: str
    activeDisruptions: int
    supplyMatchPct: float
    fleetCounts: int


class InterventionCreate(BaseModel):
    user_id: Optional[str] = None
    text: str


class InterventionRead(BaseModel):
    id: str
    user_id: Optional[str] = None
    text: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
