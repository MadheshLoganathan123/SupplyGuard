"""
Drivers endpoints — POST /drivers  GET /drivers  GET /drivers/{id}  PATCH /drivers/{id}  DELETE /drivers/{id}
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.driver import DriverCreate, DriverListResponse, DriverRead, DriverUpdate
from app.schemas.user import UserRole
from app.services.driver_service import DriverService

router = APIRouter()


@router.get(
    "/",
    response_model=DriverListResponse,
    summary="List all drivers",
    description=(
        "Returns a paginated list of drivers. "
        "Filter by `status`, `sector`, or `vehicle_type`."
    ),
)
async def list_drivers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by driver status: idle | active | en_route | offline",
    ),
    sector: Optional[str] = Query(None, description="Filter by sector (partial match)"),
    vehicle_type: Optional[str] = Query(
        None, description="Filter by vehicle type: motorcycle | cargo_bike | van | truck | drone | aerial"
    ),
    db: AsyncSession = Depends(get_db),
):
    svc = DriverService(db)
    items = await svc.get_all(
        skip=skip,
        limit=limit,
        status=status_filter,
        sector=sector,
        vehicle_type=vehicle_type,
    )
    total = await svc.count(status=status_filter)
    return DriverListResponse(total=total, items=list(items))


@router.get(
    "/{driver_id}",
    response_model=DriverRead,
    summary="Get a driver by ID",
)
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    driver = await DriverService(db).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


@router.post(
    "/",
    response_model=DriverRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new driver",
    description="Adds a new delivery driver or autonomous unit to the fleet.",
)
async def create_driver(
    payload: DriverCreate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    return await DriverService(db).create(payload)


@router.patch(
    "/{driver_id}",
    response_model=DriverRead,
    summary="Update a driver",
    description="Partial update — commonly used to update `status` or live GPS coordinates.",
)
async def update_driver(
    driver_id: str,
    payload: DriverUpdate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    svc = DriverService(db)
    driver = await svc.get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return await svc.update(driver, payload)


@router.delete(
    "/{driver_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a driver",
)
async def delete_driver(
    driver_id: str,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    svc = DriverService(db)
    driver = await svc.get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    await svc.delete(driver)
