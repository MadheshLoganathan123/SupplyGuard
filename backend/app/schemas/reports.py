from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentPerformanceRead(BaseModel):
    agent_id: str
    name: str
    efficiency_pct: float
    negotiation_speed_avg_sec: float
    route_accuracy_pct: float
    badge: Optional[str] = None
    recorded_at: Optional[datetime] = None


class ReportsMetrics(BaseModel):
    food_security_gaps_prevented: float = 12400.0
    food_security_trend_pct: float = 8.2
    price_stability_variance_pct: float = 1.4
    tons_rerouted: float = 842.0
    reroute_capacity_pct: float = 74.0
    resilience_index: float = 0.92
    last_sync: datetime


class ExportJobCreate(BaseModel):
    query: dict = Field(default_factory=dict)


class ExportJobResponse(BaseModel):
    job_id: str
    format: str
    status: str


class ExportJobRead(BaseModel):
    id: str
    format: str
    status: str
    result_data: Optional[Any] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
