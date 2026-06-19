import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dashboard_aggregator import DashboardAggregator

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_metrics(self) -> dict:
        agg = DashboardAggregator(self.db)
        try:
            return await agg.aggregate_metrics()
        except SQLAlchemyError as exc:
            logger.warning("Dashboard metrics unavailable, returning fallback values. reason=%s", exc)
            return {
                "threatLevel": "MODERATE",
                "activeDisruptions": 0,
                "supplyMatchPct": 94.0,
                "fleetCounts": 0,
            }

