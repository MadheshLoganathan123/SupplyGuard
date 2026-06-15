"""
Pydantic schemas for Shipment — request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.shipment import ShipmentStatus


class ShipmentBase(BaseModel):
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.IN_TRANSIT
    agent_id: Optional[str] = None


class ShipmentCreate(ShipmentBase):
    shipment_code: str


class ShipmentUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    agent_id: Optional[str] = None


class ShipmentRead(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    shipment_code: str
    created_at: datetime
    updated_at: datetime
