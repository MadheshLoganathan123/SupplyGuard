from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.agent_log import AgentLogRead
from app.schemas.dashboard import DashboardMetrics, InterventionCreate, InterventionRead
from app.schemas.telemetry import TelemetryCreate, TelemetryRead
from app.services.agent_log_service import AgentLogService
from app.services.dashboard_service import DashboardService
from app.services.intervention_service import InterventionService
from app.services.telemetry_service import TelemetryService

router = APIRouter()


@router.get(
    "/dashboard/metrics",
    response_model=DashboardMetrics,
    summary="Dashboard aggregated metrics",
    description="Returns threat, disruption, supply match, and fleet counts for the dashboard.",
)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    svc = DashboardService(db)
    return await svc.get_metrics()


@router.post(
    "/telemetry",
    response_model=TelemetryRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest telemetry data",
    description="Accepts node or shipment telemetry and broadcasts to connected clients.",
)
async def ingest_telemetry(
    payload: TelemetryCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = TelemetryService(db)
    telemetry = await svc.create(payload)
    await db.commit()
    return telemetry


@router.get(
    "/telemetry/recent",
    response_model=List[TelemetryRead],
    summary="Recent telemetry messages",
    description="Returns the latest node/shipment telemetry messages for the dashboard.",
)
async def get_recent_telemetry(
    limit: int = Query(50, ge=1, le=250),
    node_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = TelemetryService(db)
    return await svc.get_recent(limit=limit, node_id=node_id)


@router.get(
    "/agent-logs",
    response_model=List[AgentLogRead],
    summary="Recent agent negotiation logs",
    description="Returns paginated negotiation hub logs for AI agent decision history.",
)
async def get_agent_logs(
    limit: int = Query(50, ge=1, le=250),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentLogService(db)
    return await svc.get_recent(limit=limit)


@router.post(
    "/interventions",
    response_model=InterventionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record operator intervention",
    description="Creates an operator intervention request to queue for AI review.",
)
async def create_intervention(
    payload: InterventionCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = InterventionService(db)
    return await svc.create(payload)
