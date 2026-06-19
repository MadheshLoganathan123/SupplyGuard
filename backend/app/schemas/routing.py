from pydantic import BaseModel
from typing import List, Literal, Optional

class PathSuggestion(BaseModel):
    name: str
    dist: str
    desc: str
    efficiency: int
    color: Literal["primary", "secondary"]

class RerouteRequest(BaseModel):
    shipment_id: Optional[str] = None
    area: Optional[str] = None

class RerouteResponse(BaseModel):
    paths: List[PathSuggestion]
