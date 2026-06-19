from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.heuristic import Heuristic
from app.schemas.heuristic import HeuristicCreate


class HeuristicsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, active_only: bool = True) -> List[Heuristic]:
        query = select(Heuristic).order_by(Heuristic.created_at.desc())
        if active_only:
            query = query.where(Heuristic.active.is_(True))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_active(self) -> Optional[Heuristic]:
        result = await self.db.execute(
            select(Heuristic)
            .where(Heuristic.active.is_(True))
            .order_by(Heuristic.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: HeuristicCreate, created_by: Optional[str] = None) -> Heuristic:
        existing = await self.get_active()
        next_version = (existing.version + 1) if existing else 1

        if existing:
            existing.active = False

        heuristic = Heuristic(
            name=payload.name,
            payload=payload.payload,
            version=next_version,
            created_by=created_by,
            active=payload.active,
        )
        self.db.add(heuristic)
        await self.db.flush()
        await self.db.refresh(heuristic)
        return heuristic
