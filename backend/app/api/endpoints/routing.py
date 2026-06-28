from fastapi import APIRouter, Query
from app.schemas.routing import RerouteRequest, RerouteResponse, PathSuggestion
from app.services.routing_service import RoutingService
from app.services.reroute_job import run_reroute_job
from typing import List, Optional

router = APIRouter()

@router.post("/ai/reroute", response_model=RerouteResponse)
async def request_ai_reroute(payload: RerouteRequest):
    svc = RoutingService()
    if payload.shipment_id:
        result = await run_reroute_job(payload.shipment_id)
        paths = await svc.paths_from_reroute_result(result)
    else:
        paths = await svc.compute_alternate_paths(area=payload.area)
    return RerouteResponse(paths=paths)

@router.get("/paths/suggestions", response_model=List[PathSuggestion])
async def get_path_suggestions(area: Optional[str] = Query(None)):
    svc = RoutingService()
    return await svc.get_cached_suggestions(area)

@router.get("/computed-routes", response_model=List[PathSuggestion])
async def get_computed_routes(area: Optional[str] = Query(None), limit: int = Query(5, ge=1, le=20)):
    svc = RoutingService()
    paths = await svc.get_cached_suggestions(area)
    return paths[:limit]
