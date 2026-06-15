"""
Driver service — all DB operations for the drivers table.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate


class DriverService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count(self, status: str | None = None) -> int:
        q = select(func.count()).select_from(Driver)
        if status:
            q = q.where(Driver.status == status)
        return (await self.db.scalar(q)) or 0

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        sector: str | None = None,
        vehicle_type: str | None = None,
    ) -> Sequence[Driver]:
        q = select(Driver)
        if status:
            q = q.where(Driver.status == status)
        if sector:
            q = q.where(Driver.sector.ilike(f"%{sector}%"))
        if vehicle_type:
            q = q.where(Driver.vehicle_type == vehicle_type)
        q = q.order_by(Driver.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_by_id(self, driver_id: str) -> Driver | None:
        result = await self.db.execute(
            select(Driver).where(Driver.id == driver_id)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: DriverCreate) -> Driver:
        driver = Driver(**payload.model_dump())
        self.db.add(driver)
        await self.db.flush()
        await self.db.refresh(driver)
        return driver

    async def update(self, driver: Driver, payload: DriverUpdate) -> Driver:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(driver, field, value)
        await self.db.flush()
        await self.db.refresh(driver)
        return driver

    async def delete(self, driver: Driver) -> None:
        await self.db.delete(driver)
        await self.db.flush()
