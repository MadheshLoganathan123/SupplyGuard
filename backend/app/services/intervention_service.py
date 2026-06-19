from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intervention import Intervention
from app.schemas.dashboard import InterventionCreate


class InterventionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: InterventionCreate) -> Intervention:
        intervention = Intervention(**payload.model_dump())
        self.db.add(intervention)
        await self.db.flush()
        await self.db.refresh(intervention)
        return intervention
