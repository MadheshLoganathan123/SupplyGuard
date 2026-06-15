"""
Farmer service — all DB operations for the farmers table.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerUpdate


class FarmerService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count(self, active_only: bool = False) -> int:
        q = select(func.count()).select_from(Farmer)
        if active_only:
            q = q.where(Farmer.is_active == True)  # noqa: E712
        return (await self.db.scalar(q)) or 0

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        sector: str | None = None,
        active_only: bool = False,
    ) -> Sequence[Farmer]:
        q = select(Farmer)
        if sector:
            q = q.where(Farmer.sector.ilike(f"%{sector}%"))
        if active_only:
            q = q.where(Farmer.is_active == True)  # noqa: E712
        q = q.order_by(Farmer.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, farmer_id: str) -> Farmer | None:
        result = await self.db.execute(
            select(Farmer).where(Farmer.id == farmer_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: FarmerCreate) -> Farmer:
        farmer = Farmer(**payload.model_dump())
        self.db.add(farmer)
        await self.db.flush()
        await self.db.refresh(farmer)
        return farmer

    async def update(self, farmer: Farmer, payload: FarmerUpdate) -> Farmer:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(farmer, field, value)
        await self.db.flush()
        await self.db.refresh(farmer)
        return farmer

    async def delete(self, farmer: Farmer) -> None:
        await self.db.delete(farmer)
        await self.db.flush()
