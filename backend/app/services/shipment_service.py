"""
Shipment service — business logic layer between API and database.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate


class ShipmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Shipment]:
        result = await self.db.execute(
            select(Shipment).offset(skip).limit(limit).order_by(Shipment.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, shipment_id: str) -> Shipment | None:
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Shipment | None:
        result = await self.db.execute(
            select(Shipment).where(Shipment.shipment_code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: ShipmentStatus) -> Sequence[Shipment]:
        result = await self.db.execute(
            select(Shipment).where(Shipment.status == status)
        )
        return result.scalars().all()

    async def create(self, payload: ShipmentCreate) -> Shipment:
        shipment = Shipment(**payload.model_dump())
        self.db.add(shipment)
        await self.db.flush()
        await self.db.refresh(shipment)
        return shipment

    async def update(self, shipment: Shipment, payload: ShipmentUpdate) -> Shipment:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(shipment, field, value)
        await self.db.flush()
        await self.db.refresh(shipment)
        return shipment

    async def delete(self, shipment: Shipment) -> None:
        await self.db.delete(shipment)
        await self.db.flush()
