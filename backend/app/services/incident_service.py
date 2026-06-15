"""
Incident service — business logic for supply chain disruptions.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentStatus
from app.schemas.incident import IncidentCreate, IncidentUpdate


class IncidentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Incident]:
        result = await self.db.execute(
            select(Incident)
            .offset(skip)
            .limit(limit)
            .order_by(Incident.occurred_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, incident_id: str) -> Incident | None:
        result = await self.db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def get_open(self) -> Sequence[Incident]:
        result = await self.db.execute(
            select(Incident).where(Incident.status == IncidentStatus.OPEN)
        )
        return result.scalars().all()

    async def create(self, payload: IncidentCreate) -> Incident:
        incident = Incident(**payload.model_dump())
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident

    async def update(self, incident: Incident, payload: IncidentUpdate) -> Incident:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(incident, field, value)
        await self.db.flush()
        await self.db.refresh(incident)
        return incident
