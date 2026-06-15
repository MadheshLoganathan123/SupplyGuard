"""
Store service — all DB operations for the stores table.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate


class StoreService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count(self, active_only: bool = False) -> int:
        q = select(func.count()).select_from(Store)
        if active_only:
            q = q.where(Store.is_active == True)  # noqa: E712
        return (await self.db.scalar(q)) or 0

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        sector: str | None = None,
        store_type: str | None = None,
        active_only: bool = False,
    ) -> Sequence[Store]:
        q = select(Store)
        if sector:
            q = q.where(Store.sector.ilike(f"%{sector}%"))
        if store_type:
            q = q.where(Store.store_type == store_type)
        if active_only:
            q = q.where(Store.is_active == True)  # noqa: E712
        q = q.order_by(Store.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, store_id: str) -> Store | None:
        result = await self.db.execute(
            select(Store).where(Store.id == store_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: StoreCreate) -> Store:
        store = Store(**payload.model_dump())
        self.db.add(store)
        await self.db.flush()
        await self.db.refresh(store)
        return store

    async def update(self, store: Store, payload: StoreUpdate) -> Store:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(store, field, value)
        await self.db.flush()
        await self.db.refresh(store)
        return store

    async def delete(self, store: Store) -> None:
        await self.db.delete(store)
        await self.db.flush()
