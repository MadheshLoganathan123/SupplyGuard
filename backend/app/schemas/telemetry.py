from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TelemetryRead(BaseModel):
    id: str
    node_id: Optional[str] = None
    shipment_id: Optional[str] = None
    type: str
    payload: Any
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TelemetryCreate(BaseModel):
    node_id: Optional[str] = None
    shipment_id: Optional[str] = None
    type: str
    payload: dict

