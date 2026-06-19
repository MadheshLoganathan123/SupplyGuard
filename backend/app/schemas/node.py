from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NodeConnection(BaseModel):
    name: str
    type: str
    status: str
    eta: str


class NodeSummary(BaseModel):
    id: str
    name: str
    node_type: str
    status: str
    agent_name: Optional[str] = None
    image_url: Optional[str] = None
    inventory_label: Optional[str] = None
    threat_level: Optional[str] = None
    throughput: Optional[str] = None
    position_index: int = 0

    model_config = ConfigDict(from_attributes=True)


class NodeStatusCounts(BaseModel):
    operational: int = 0
    at_risk: int = 0
    blocked: int = 0
    inactive: int = 0


class NetworkMetrics(BaseModel):
    latency_ms: float = 24.0
    negotiation_success_pct: float = 97.7
    supply_demand_gap_pct: float = 4.2


class NodeListResponse(BaseModel):
    status_counts: NodeStatusCounts
    metrics: NetworkMetrics
    nodes: List[NodeSummary]


class NodeDetail(NodeSummary):
    inventory_level: Optional[float] = None
    sector: Optional[str] = None
    connections: List[NodeConnection] = Field(default_factory=list)
    recent_telemetry: List[Any] = Field(default_factory=list)
