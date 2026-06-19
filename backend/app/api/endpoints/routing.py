from fastapi import APIRouter, Query
from app.schemas.routing import RerouteRequest, RerouteResponse, PathSuggestion
from app.services.routing_service import RoutingService
from typing import List, Optional

router = APIRouter()

@router.post("/ai/reroute", response_model=RerouteResponse)
async def request_ai_reroute(payload: RerouteRequest):
    svc = RoutingService()
    paths = await svc.compute_alternate_paths()
    return RerouteResponse(paths=paths)

@router.get("/paths/suggestions", response_model=List[PathSuggestion])
async def get_path_suggestions(area: Optional[str] = Query(None)):
    svc = RoutingService()
    return await svc.get_cached_suggestions(area)
