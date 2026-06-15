"""
Inventory endpoints — POST /inventory  GET /inventory  GET /inventory/{id}  PATCH /inventory/{id}  DELETE /inventory/{id}
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.inventory import (
    InventoryCreate,
    InventoryListResponse,
    InventoryRead,
    InventoryUpdate,
)
from app.schemas.user import UserRole
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.get(
    "/",
    response_model=InventoryListResponse,
    summary="List inventory",
    description=(
        "Returns paginated inventory records. "
        "Filter by owner (`farmer_id`, `store_id`, `pantry_id`), `category`, or `low_stock_only`."
    ),
)
async def list_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    farmer_id: Optional[str] = Query(None, description="Filter by farmer UUID"),
    store_id: Optional[str] = Query(None, description="Filter by store UUID"),
    pantry_id: Optional[str] = Query(None, description="Filter by pantry UUID"),
    category: Optional[str] = Query(
        None,
        description="Filter by category: grain | produce | dairy | protein | medical | water | general",
    ),
    low_stock_only: bool = Query(
        False, description="Return only items at or below their minimum threshold"
    ),
    db: AsyncSession = Depends(get_db),
):
    svc = InventoryService(db)
    items = await svc.get_all(
        skip=skip,
        limit=limit,
        farmer_id=farmer_id,
        store_id=store_id,
        pantry_id=pantry_id,
        category=category,
        low_stock_only=low_stock_only,
    )
    total = await svc.count(
        farmer_id=farmer_id, store_id=store_id, pantry_id=pantry_id
    )
    return InventoryListResponse(total=total, items=list(items))


@router.get(
    "/{inventory_id}",
    response_model=InventoryRead,
    summary="Get an inventory item by ID",
)
async def get_inventory_item(inventory_id: str, db: AsyncSession = Depends(get_db)):
    item = await InventoryService(db).get_by_id(inventory_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found"
        )
    return item


@router.post(
    "/",
    response_model=InventoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an inventory item",
    description=(
        "Creates a new inventory record. "
        "Exactly one of `farmer_id`, `store_id`, or `pantry_id` must be provided."
    ),
)
async def create_inventory_item(
    payload: InventoryCreate,
    current_user: AuthUser = Depends(
        require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])
    ),
    db: AsyncSession = Depends(get_db),
):
    return await InventoryService(db).create(payload)


@router.patch(
    "/{inventory_id}",
    response_model=InventoryRead,
    summary="Update an inventory item",
    description="Partial update — typically used to adjust `quantity` after a delivery.",
)
async def update_inventory_item(
    inventory_id: str,
    payload: InventoryUpdate,
    current_user: AuthUser = Depends(
        require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])
    ),
    db: AsyncSession = Depends(get_db),
):
    svc = InventoryService(db)
    item = await svc.get_by_id(inventory_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found"
        )
    return await svc.update(item, payload)


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an inventory item",
)
async def delete_inventory_item(
    inventory_id: str,
    current_user: AuthUser = Depends(
        require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])
    ),
    db: AsyncSession = Depends(get_db),
):
    svc = InventoryService(db)
    item = await svc.get_by_id(inventory_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found"
        )
    await svc.delete(item)
