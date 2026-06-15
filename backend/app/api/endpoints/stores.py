"""
Stores endpoints — POST /stores  GET /stores  GET /stores/{id}  PATCH /stores/{id}  DELETE /stores/{id}
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.store import StoreCreate, StoreListResponse, StoreRead, StoreUpdate
from app.schemas.user import UserRole
from app.services.store_service import StoreService

router = APIRouter()


@router.get(
    "/",
    response_model=StoreListResponse,
    summary="List all stores",
    description=(
        "Returns a paginated list of retail/wholesale stores. "
        "Filter by `sector`, `store_type`, or `active_only`."
    ),
)
async def list_stores(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    sector: Optional[str] = Query(None, description="Filter by sector (partial match)"),
    store_type: Optional[str] = Query(
        None,
        description="Filter by type: retail | wholesale | cooperative | emergency_hub",
    ),
    active_only: bool = Query(False, description="Return only active stores"),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    items = await svc.get_all(
        skip=skip,
        limit=limit,
        sector=sector,
        store_type=store_type,
        active_only=active_only,
    )
    total = await svc.count(active_only=active_only)
    return StoreListResponse(total=total, items=list(items))


@router.get(
    "/{store_id}",
    response_model=StoreRead,
    summary="Get a store by ID",
)
async def get_store(store_id: str, db: AsyncSession = Depends(get_db)):
    store = await StoreService(db).get_by_id(store_id)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store


@router.post(
    "/",
    response_model=StoreRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new store",
    description="Creates a new retail, wholesale, or emergency hub distribution point.",
)
async def create_store(
    payload: StoreCreate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    return await StoreService(db).create(payload)


@router.patch(
    "/{store_id}",
    response_model=StoreRead,
    summary="Update a store",
    description="Partial update — only provided fields are changed.",
)
async def update_store(
    store_id: str,
    payload: StoreUpdate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    store = await svc.get_by_id(store_id)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return await svc.update(store, payload)


@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a store",
)
async def delete_store(
    store_id: str,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_OWNER, UserRole.PANTRY_MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    svc = StoreService(db)
    store = await svc.get_by_id(store_id)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    await svc.delete(store)
