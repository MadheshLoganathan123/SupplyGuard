"""
Pydantic schemas for Incident.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    sector: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    resolved_at: Optional[datetime] = None


class IncidentRead(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    occurred_at: datetime
    resolved_at: Optional[datetime] = None
