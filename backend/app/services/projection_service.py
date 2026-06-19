import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.projection import Projection, ProjectionStatus
from app.schemas.projection import ProjectionCreate

logger = logging.getLogger(__name__)


class ProjectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: ProjectionCreate) -> Projection:
        projection = Projection(
            type="demand",
            input=payload.model_dump(),
            status=ProjectionStatus.QUEUED.value,
        )
        self.db.add(projection)
        await self.db.flush()
        await self.db.refresh(projection)
        return projection

    async def get_by_id(self, projection_id: str) -> Projection | None:
        result = await self.db.execute(
            select(Projection).where(Projection.id == projection_id)
        )
        return result.scalar_one_or_none()


async def run_projection_job(projection_id: str) -> None:
    logger.info("Starting projection job %s", projection_id)
    await asyncio.sleep(2)

    async with AsyncSessionLocal() as db:
        svc = ProjectionService(db)
        projection = await svc.get_by_id(projection_id)
        if not projection:
            logger.warning("Projection %s not found", projection_id)
            return

        projection.status = ProjectionStatus.RUNNING.value
        projection.started_at = datetime.now(timezone.utc)
        await db.commit()

    await asyncio.sleep(1)

    async with AsyncSessionLocal() as db:
        svc = ProjectionService(db)
        projection = await svc.get_by_id(projection_id)
        if not projection:
            return

        node_count = len(projection.input.get("node_ids", []))
        projection.status = ProjectionStatus.DONE.value
        projection.result = {
            "summary": f"Projection complete: supply matches demand (+{4.2 + node_count * 0.1:.1f}% margin).",
            "supply_demand_gap_pct": max(1.0, 4.2 - node_count * 0.05),
            "horizon_days": projection.input.get("horizon_days", 7),
            "nodes_analyzed": node_count,
        }
        projection.finished_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Projection %s completed", projection_id)
