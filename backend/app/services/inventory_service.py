"""
Inventory service — all DB operations for the inventory table.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate


class InventoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count(
        self,
        farmer_id: str | None = None,
        store_id: str | None = None,
        pantry_id: str | None = None,
    ) -> int:
        q = select(func.count()).select_from(Inventory)
        if farmer_id:
            q = q.where(Inventory.farmer_id == farmer_id)
        if store_id:
            q = q.where(Inventory.store_id == store_id)
        if pantry_id:
            q = q.where(Inventory.pantry_id == pantry_id)
        return (await self.db.scalar(q)) or 0

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        farmer_id: str | None = None,
        store_id: str | None = None,
        pantry_id: str | None = None,
        category: str | None = None,
        low_stock_only: bool = False,
    ) -> Sequence[Inventory]:
        q = select(Inventory)
        if farmer_id:
            q = q.where(Inventory.farmer_id == farmer_id)
        if store_id:
            q = q.where(Inventory.store_id == store_id)
        if pantry_id:
            q = q.where(Inventory.pantry_id == pantry_id)
        if category:
            q = q.where(Inventory.category == category)
        if low_stock_only:
            # quantity at or below the minimum threshold
            q = q.where(Inventory.quantity <= Inventory.min_threshold)
        q = q.order_by(Inventory.updated_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, inventory_id: str) -> Inventory | None:
        result = await self.db.execute(
            select(Inventory).where(Inventory.id == inventory_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: InventoryCreate) -> Inventory:
        inventory = Inventory(**payload.model_dump())
        self.db.add(inventory)
        await self.db.flush()
        await self.db.refresh(inventory)
        return inventory

    async def update(self, inventory: Inventory, payload: InventoryUpdate) -> Inventory:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(inventory, field, value)
        await self.db.flush()
        await self.db.refresh(inventory)
        return inventory

    async def delete(self, inventory: Inventory) -> None:
        await self.db.delete(inventory)
        await self.db.flush()
