"""
Farmers endpoints — POST /farmers  GET /farmers  GET /farmers/{id}  PATCH /farmers/{id}  DELETE /farmers/{id}
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.farmer import FarmerCreate, FarmerListResponse, FarmerRead, FarmerUpdate
from app.schemas.user import UserRole
from app.services.farmer_service import FarmerService

router = APIRouter()


@router.get(
    "/",
    response_model=FarmerListResponse,
    summary="List all farmers",
    description=(
        "Returns a paginated list of farmers. "
        "Filter by `sector`, `farm_type`, or `active_only`."
    ),
)
async def list_farmers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    sector: Optional[str] = Query(None, description="Filter by sector name (partial match)"),
    active_only: bool = Query(False, description="Return only active farmers"),
    db: AsyncSession = Depends(get_db),
):
    svc = FarmerService(db)
    items = await svc.get_all(skip=skip, limit=limit, sector=sector, active_only=active_only)
    total = await svc.count(active_only=active_only)
    return FarmerListResponse(total=total, items=list(items))


@router.get(
    "/{farmer_id}",
    response_model=FarmerRead,
    summary="Get a farmer by ID",
)
async def get_farmer(farmer_id: str, db: AsyncSession = Depends(get_db)):
    farmer = await FarmerService(db).get_by_id(farmer_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.post(
    "/",
    response_model=FarmerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farmer",
    description="Creates a new farmer / agricultural supply node.",
)
async def create_farmer(
    payload: FarmerCreate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER])),
    db: AsyncSession = Depends(get_db),
):
    return await FarmerService(db).create(payload)


@router.patch(
    "/{farmer_id}",
    response_model=FarmerRead,
    summary="Update a farmer",
    description="Partial update — only provided fields are changed.",
)
async def update_farmer(
    farmer_id: str,
    payload: FarmerUpdate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER])),
    db: AsyncSession = Depends(get_db),
):
    svc = FarmerService(db)
    farmer = await svc.get_by_id(farmer_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return await svc.update(farmer, payload)


@router.delete(
    "/{farmer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a farmer",
)
async def delete_farmer(
    farmer_id: str,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER])),
    db: AsyncSession = Depends(get_db),
):
    svc = FarmerService(db)
    farmer = await svc.get_by_id(farmer_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    await svc.delete(farmer)
