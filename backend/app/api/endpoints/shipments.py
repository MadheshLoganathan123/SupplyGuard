"""
Shipments API endpoints — CRUD + status filter.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.shipment import ShipmentStatus
from app.schemas.agent_log import AgentLogCreate
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
from app.services.log_service import LogService
from app.services.shipment_service import ShipmentService
from app.services.reroute_job import run_reroute_job

router = APIRouter()


@router.get("/", response_model=List[ShipmentRead])
async def list_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: ShipmentStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = ShipmentService(db)
    if status:
        return await svc.get_by_status(status)
    return await svc.get_all(skip=skip, limit=limit)


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def get_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    svc = ShipmentService(db)
    shipment = await svc.get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.post(
    "/",
    response_model=ShipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shipment",
    description="Requires authenticated user with a permitted logistics role.",
)
async def create_shipment(
    payload: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = ShipmentService(db)
    existing = await svc.get_by_code(payload.shipment_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Shipment code '{payload.shipment_code}' already exists",
        )
    shipment = await svc.create(payload)

    agent_label = payload.agent_name or (shipment.agent.name if shipment.agent else "Logistics")
    log_svc = LogService(db)
    await log_svc.create_log(
        AgentLogCreate(
            agent_name=agent_label,
            agent_type="logistics",
            action_type="CREATE_SHIPMENT",
            message=(
                f"Dispatched {shipment.shipment_code}: "
                f"{shipment.origin} -> {shipment.destination} [{shipment.status.value}]"
            ),
            payload={
                "shipment_id": shipment.id,
                "shipment_code": shipment.shipment_code,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "status": shipment.status.value,
            },
        )
    )

    return shipment


@router.patch("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: str,
    payload: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    svc = ShipmentService(db)
    shipment = await svc.get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return await svc.update(shipment, payload)


@router.post("/{shipment_id}/trigger-reroute", response_model=ShipmentRead)
async def trigger_reroute(
    shipment_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    svc = ShipmentService(db)
    shipment = await svc.get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    
    background_tasks.add_task(run_reroute_job, shipment.id)
    return shipment


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: str, db: AsyncSession = Depends(get_db)):
    svc = ShipmentService(db)
    shipment = await svc.get_by_id(shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    await svc.delete(shipment)
