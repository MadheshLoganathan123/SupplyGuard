from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectionCreate(BaseModel):
    node_ids: List[str] = Field(default_factory=list)
    horizon_days: int = Field(default=7, ge=1, le=90)
    params: dict = Field(default_factory=dict)


class ProjectionJobResponse(BaseModel):
    job_id: str


class ProjectionRead(BaseModel):
    id: str
    type: str
    input: dict
    result: Optional[dict] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
