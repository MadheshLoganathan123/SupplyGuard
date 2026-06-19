from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class HeuristicCreate(BaseModel):
    name: str = "default_calibration"
    payload: dict = Field(default_factory=dict)
    active: bool = True


class HeuristicRead(BaseModel):
    id: str
    name: str
    payload: dict
    version: int
    created_by: Optional[str] = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
