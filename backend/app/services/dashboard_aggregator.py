from sqlalchemy import select, func
from sqlalchemy.exc import DBAPIError, NoSuchTableError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.incident import Incident, IncidentStatus
from app.models.driver import Driver
from app.models.inventory import Inventory
from app.models.shipment import Shipment, ShipmentStatus
import logging

logger = logging.getLogger(__name__)


class DashboardAggregator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def safe_scalar(self, statement):
        try:
            return await self.db.scalar(statement)
        except (NoSuchTableError, ProgrammingError, DBAPIError) as exc:
            logger.warning(
                "Dashboard metric query failed; defaulting metric to 0. reason=%s", exc
            )
            await self.db.rollback()
            return 0

    async def aggregate_metrics(self) -> dict:
        # 1. Count active disruptions (OPEN status)
        active_disruptions = await self.safe_scalar(
            select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.OPEN)
        ) or 0

        # 2. Count total driver fleet
        fleet_counts = await self.safe_scalar(
            select(func.count()).select_from(Driver)
        ) or 0

        # 3. Count low stock items (quantity <= min_threshold)
        low_stock_count = await self.safe_scalar(
            select(func.count()).select_from(Inventory).where(Inventory.quantity <= Inventory.min_threshold)
        ) or 0

        # 4. Count delayed or rerouted shipments
        disrupted_shipments = await self.safe_scalar(
            select(func.count()).select_from(Shipment).where(
                Shipment.status.in_([ShipmentStatus.DELAYED, ShipmentStatus.REROUTED])
            )
        ) or 0

        # 5. Compute global threat level
        # CRITICAL if active disruptions > 3 or disrupted shipments > 2
        # ELEVATED if active disruptions > 0 or low stock count > 2 or disrupted shipments > 0
        # MODERATE otherwise
        if active_disruptions > 3 or disrupted_shipments > 2:
            threat_level = "CRITICAL"
        elif active_disruptions > 0 or low_stock_count > 2 or disrupted_shipments > 0:
            threat_level = "ELEVATED"
        else:
            threat_level = "MODERATE"

        # 6. Compute supply match percentage
        total_inventory_items = await self.safe_scalar(
            select(func.count()).select_from(Inventory)
        ) or 0

        if total_inventory_items > 0:
            supply_match_pct = float(
                round(((total_inventory_items - low_stock_count) / total_inventory_items) * 100, 1)
            )
        else:
            supply_match_pct = 94.0  # fallback static baseline from UI

        return {
            "threatLevel": threat_level,
            "activeDisruptions": int(active_disruptions),
            "supplyMatchPct": supply_match_pct,
            "fleetCounts": int(fleet_counts),
        }
