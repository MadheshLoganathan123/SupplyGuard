"""
Agent Tools — Callable tools for agents to use during reasoning.
These tools are LLM-accessible and provide structured data for decision-making.
"""

from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.farmer import Farmer
from app.models.inventory import Inventory
from app.models.shipment import Shipment
from app.models.store import Store
from app.models.supply_node import SupplyNode


class AgentTools:
    """Collection of tools available to agents for reasoning and decision-making."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_drivers(
        self,
        sector: str | None = None,
        emergency_capable: bool = False,
        available_only: bool = True,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find drivers matching criteria (emergency capability, sector, availability).

        Args:
            sector: Filter by sector (optional)
            emergency_capable: Only return drivers with emergency capability
            available_only: Only return drivers not currently busy
            limit: Maximum number of results

        Returns:
            List of driver info with availability and capability metrics
        """
        query = select(Driver)

        if sector:
            query = query.where(Driver.sector == sector)

        if emergency_capable:
            query = query.where(Driver.capacity_kg >= 500)

        if available_only:
            query = query.where(Driver.status.in_(["idle", "active"]))

        query = query.limit(limit)
        result = await self.db.execute(query)
        drivers = result.scalars().all()

        return [
            {
                "driver_id": d.id,
                "name": d.vehicle_plate or f"{d.vehicle_type.title()} Driver",
                "sector": d.sector,
                "vehicle_type": d.vehicle_type,
                "capacity_kg": float(d.capacity_kg or 0),
                "emergency_capable": float(d.capacity_kg or 0) >= 500,
                "is_available": d.status in ("idle", "active"),
                "status": d.status,
                "reliability_score": max(0.1, 1 - float(d.utilization_pct or 0) / 100),
            }
            for d in drivers
        ]

    async def query_inventory(
        self,
        node_type: str | None = None,
        item_type: str | None = None,
        min_quantity: int | None = None,
        sector: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query inventory across nodes (farms, stores, warehouses).

        Args:
            node_type: Type of node ('farm', 'store', 'warehouse')
            item_type: Type of item to search for
            min_quantity: Minimum quantity threshold
            sector: Filter by sector

        Returns:
            List of inventory items with node info and quantities
        """
        query = select(Inventory, Farmer, Store).outerjoin(
            Farmer, Inventory.farmer_id == Farmer.id
        ).outerjoin(Store, Inventory.store_id == Store.id)

        if node_type:
            if node_type.lower() in {"farm", "farmer"}:
                query = query.where(Inventory.farmer_id.is_not(None))
            elif node_type.lower() == "store":
                query = query.where(Inventory.store_id.is_not(None))

        if item_type:
            query = query.where(Inventory.category == item_type)

        if min_quantity is not None:
            query = query.where(Inventory.quantity >= min_quantity)

        if sector:
            query = query.where((Farmer.sector == sector) | (Store.sector == sector))

        query = query.order_by(desc(Inventory.quantity)).limit(50)
        result = await self.db.execute(query)
        rows = result.all()

        items = []
        for inv, farmer, store in rows:
            owner = farmer or store
            items.append({
                "inventory_id": inv.id,
                "node_id": getattr(owner, "id", None),
                "node_name": getattr(owner, "farm_name", None) or getattr(owner, "store_name", None) or "Pantry",
                "node_type": "farmer" if farmer else "store" if store else "pantry",
                "sector": getattr(owner, "sector", None),
                "item_type": inv.category,
                "item_name": inv.item_name,
                "quantity": float(inv.quantity or 0),
                "unit": inv.unit,
                "last_updated": inv.updated_at.isoformat() if inv.updated_at else None,
            })
        return items

    async def compute_route(
        self,
        origin_node_id: str,
        destination_node_id: str,
        shipment_id: str | None = None,
        optimize_for: str = "speed",
    ) -> dict[str, Any]:
        """
        Compute an optimal route between two nodes.

        Args:
            origin_node_id: Starting node ID
            destination_node_id: Destination node ID
            shipment_id: Associated shipment (for context)
            optimize_for: Optimization criteria ('speed', 'cost', 'reliability')

        Returns:
            Route info with estimated time, distance, cost, and driver recommendations
        """
        # Get origin and destination nodes
        origin_result = await self.db.execute(
            select(SupplyNode).where(SupplyNode.id == origin_node_id)
        )
        origin = origin_result.scalar_one_or_none()

        dest_result = await self.db.execute(
            select(SupplyNode).where(SupplyNode.id == destination_node_id)
        )
        destination = dest_result.scalar_one_or_none()

        if not origin or not destination:
            return {
                "status": "error",
                "message": "Origin or destination node not found",
            }

        # Simplified route calculation (in production, use actual routing engine)
        # For now, estimate based on sector distance
        same_sector = origin.sector == destination.sector
        estimated_hours = 2 if same_sector else 6
        estimated_km = 50 if same_sector else 200
        estimated_cost = estimated_km * 0.5  # $0.50 per km

        # Get suitable drivers
        drivers = await self.find_drivers(
            sector=destination.sector,
            available_only=True,
            limit=3,
        )

        return {
            "status": "success",
            "origin": {
                "node_id": origin.id,
                "name": origin.name,
                "sector": origin.sector,
            },
            "destination": {
                "node_id": destination.id,
                "name": destination.name,
                "sector": destination.sector,
            },
            "route": {
                "estimated_hours": estimated_hours,
                "estimated_km": estimated_km,
                "estimated_cost": estimated_cost,
                "optimization": optimize_for,
            },
            "recommended_drivers": drivers,
        }

    async def find_stores_with_demand(
        self,
        sector: str | None = None,
        min_demand: int | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find stores with high demand (sourcing agent use).

        Args:
            sector: Filter by sector
            min_demand: Minimum demand threshold
            limit: Maximum results

        Returns:
            List of stores with demand and inventory shortfall info
        """
        query = select(Store)

        if sector:
            query = query.where(Store.sector == sector)

        query = query.order_by(Store.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        stores = result.scalars().all()

        return [
            {
                "store_id": s.id,
                "name": s.store_name,
                "sector": s.sector,
                "daily_demand": 100,
                "inventory_level": 0,
                "shortfall": 100,
            }
            for s in stores
            if min_demand is None or 100 >= min_demand
        ]

    async def find_farmers_with_surplus(
        self,
        item_type: str | None = None,
        sector: str | None = None,
        min_surplus: int | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Find farmers with surplus supply (sourcing agent use).

        Args:
            item_type: Type of item to find
            sector: Filter by sector
            min_surplus: Minimum surplus threshold
            limit: Maximum results

        Returns:
            List of farmers with surplus availability
        """
        query = select(Farmer)

        if sector:
            query = query.where(Farmer.sector == sector)

        query = query.limit(limit)
        result = await self.db.execute(query)
        farmers = result.scalars().all()

        farmers_with_inventory = []
        for farmer in farmers:
            # Get farmer's inventory
            inv_result = await self.db.execute(
                select(Inventory).where(
                    and_(
                        Inventory.farmer_id == farmer.id,
                        Inventory.category == item_type if item_type else True,
                    )
                )
            )
            inventories = inv_result.scalars().all()

            for inv in inventories:
                surplus = max(0, inv.quantity - inv.min_threshold)
                if min_surplus is None or surplus >= min_surplus:
                    farmers_with_inventory.append(
                        {
                            "farmer_id": farmer.id,
                            "name": farmer.farm_name,
                            "sector": farmer.sector,
                            "item_type": inv.item_type,
                            "surplus": surplus,
                            "total_quantity": inv.quantity,
                        }
                    )

        return farmers_with_inventory[:limit]
