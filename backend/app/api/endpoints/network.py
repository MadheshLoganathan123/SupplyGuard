"""
Network health / telemetry endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.agent import Agent, AgentStatus
from app.models.incident import Incident, IncidentStatus
from app.models.shipment import Shipment, ShipmentStatus

router = APIRouter()


@router.get("/health")
async def network_health(db: AsyncSession = Depends(get_db)):
    """Aggregate telemetry snapshot for the dashboard."""

    # Active agent count
    active_agents = await db.scalar(
        select(func.count()).where(Agent.status == AgentStatus.ACTIVE)
    )

    # Open incidents
    open_incidents = await db.scalar(
        select(func.count()).where(Incident.status == IncidentStatus.OPEN)
    )

    # Rerouted shipments
    rerouted = await db.scalar(
        select(func.count()).where(Shipment.status == ShipmentStatus.REROUTED)
    )

    return {
        "active_agents": active_agents or 0,
        "open_incidents": open_incidents or 0,
        "rerouted_shipments": rerouted or 0,
        "threat_level": "ELEVATED" if (open_incidents or 0) > 2 else "MODERATE",
        "supply_match_pct": 94.0,   # placeholder — replace with real calculation
        "network_fleet": 142,       # placeholder
    }
