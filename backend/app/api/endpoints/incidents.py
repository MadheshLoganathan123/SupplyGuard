"""
Incidents API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.user import UserRole
from app.services.incident_service import IncidentService

router = APIRouter()


@router.get("/", response_model=List[IncidentRead])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    open_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    svc = IncidentService(db)
    if open_only:
        return await svc.get_open()
    return await svc.get_all(skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    svc = IncidentService(db)
    incident = await svc.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post(
    "/",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Report a disruption event",
    description="Requires an authenticated user with a valid platform role.",
)
async def create_incident(
    payload: IncidentCreate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.DRIVER, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    return await IncidentService(db).create(payload)


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.DRIVER, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    svc = IncidentService(db)
    incident = await svc.get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return await svc.update(incident, payload)
