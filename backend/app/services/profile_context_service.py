"""
ProfileContextService — builds rich context for agent decisions using profile data.

Aggregates driver, farmer, store, and shipment profiles into a single
AgentContext with threat level, inventory status, and demand metrics.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentContext
from app.models.shipment import Shipment
from app.services.inventory_service import InventoryService
from app.services.profile_service import ProfileService

logger = logging.getLogger(__name__)


class ProfileContextService:
    """
    Builds rich AgentContext by aggregating:
    - Shipment origin/destination
    - Driver profiles (vehicle_type, capacity, operating_radius, emergency_ready)
    - Farmer profiles (crops, available_qty, self_delivery, trust_score)
    - Store profiles (avg_demand, accepting_emergency, cold_storage)
    - Incident data (active incidents in sector)
    - Inventory levels (current stock, reorder points)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.profile_service = ProfileService(db_session=db)
        self.inventory_service = InventoryService(db)

    async def build_context(
        self,
        shipment: Shipment,
        incident_ids: Optional[List[str]] = None,
    ) -> AgentContext:
        """
        Build a comprehensive AgentContext for a shipment.

        Args:
            shipment: Shipment object to build context for
            incident_ids: List of active incident IDs in the sector

        Returns:
            AgentContext with sector, threat_level, incidents, and rich metadata
        """
        try:
            # Step 1: Extract sector from shipment destination
            sector = self._extract_sector(shipment.destination)
            logger.debug(f"Building context for shipment {shipment.shipment_code} in sector {sector}")

            # Step 2: Assess threat level from incidents
            threat_level = await self._assess_threat_level(
                sector=sector,
                incident_ids=incident_ids or [],
            )

            # Step 3: Fetch profiles (driver, farmer, store)
            origin_profiles = await self._fetch_location_profiles(shipment.origin)
            destination_profiles = await self._fetch_location_profiles(shipment.destination)

            # Step 4: Get inventory status
            inventory_status = await self._get_inventory_status(sector)

            # Step 5: Assess sector demand level
            sector_demand_level = await self._assess_sector_demand(
                sector=sector,
                destination_profiles=destination_profiles,
            )

            # Step 6: Build metadata with all profile data
            metadata = {
                "shipment_id": shipment.id,
                "shipment_code": shipment.shipment_code,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "origin_profiles": origin_profiles,
                "destination_profiles": destination_profiles,
                "inventory_status": inventory_status,
                "sector_demand_level": sector_demand_level,
                "driver_availability": await self._get_driver_availability(sector),
                "store_capacity": await self._get_store_capacity(sector),
                "farmer_surplus": await self._get_farmer_surplus(sector),
            }

            context = AgentContext(
                sector=sector,
                threat_level=threat_level,
                active_incidents=incident_ids or [],
                metadata=metadata,
            )

            logger.info(
                f"Context built: sector={sector}, threat_level={threat_level}, "
                f"incidents={len(context.active_incidents)}"
            )

            # Attach to context for easy access in agents
            context.inventory_status = inventory_status
            context.sector_demand_level = sector_demand_level

            return context

        except Exception as e:
            logger.exception(f"Error building context for shipment {shipment.id}: {e}")
            # Return a default safe context
            return AgentContext(
                sector="UNKNOWN",
                threat_level="NORMAL",
                active_incidents=[],
                metadata={"error": str(e)},
            )

    async def _assess_threat_level(
        self,
        sector: str,
        incident_ids: List[str],
    ) -> str:
        """
        Assess threat level based on incident count and severity.

        Args:
            sector: Sector identifier
            incident_ids: List of active incident IDs

        Returns:
            Threat level: "NORMAL", "ELEVATED", or "CRITICAL"
        """
        if not incident_ids:
            return "NORMAL"

        # In production: fetch incident records and check severity
        incident_count = len(incident_ids)
        if incident_count >= 3:
            return "CRITICAL"
        elif incident_count >= 1:
            return "ELEVATED"
        return "NORMAL"

    def _extract_sector(self, location: str) -> str:
        """Extract sector identifier from location string (e.g., 'North', 'East')."""
        # Simple implementation: assume sector is first word
        # In production: use a location→sector mapping service
        parts = location.split()
        return parts[0].upper() if parts else "CENTRAL"

    async def _fetch_location_profiles(self, location: str) -> Dict[str, Any]:
        """
        Fetch all available profiles (driver, farmer, store) for a location.

        Returns a dict with lists of profiles:
        {
            "drivers": [...],
            "farmers": [...],
            "stores": [...],
        }
        """
        profiles = {
            "drivers": [],
            "farmers": [],
            "stores": [],
        }

        try:
            profiles["drivers"] = await self.profile_service.discover_drivers()
            profiles["farmers"] = await self.profile_service.discover_farmers()
            profiles["stores"] = await self.profile_service.discover_stores()

            logger.debug(
                f"Fetched profiles for {location}: "
                f"{len(profiles['drivers'])} drivers, "
                f"{len(profiles['farmers'])} farmers, "
                f"{len(profiles['stores'])} stores"
            )

        except Exception as e:
            logger.warning(f"Error fetching profiles for {location}: {e}")

        return profiles

    async def _get_inventory_status(self, sector: str) -> str:
        """
        Get overall inventory status for a sector.

        Returns: "LOW", "NORMAL", or "HIGH"
        """
        try:
            # Simplified: in production, aggregate inventory by sector
            total = await self.inventory_service.get_total_quantity(sector)
            reorder_point = 1000  # Example threshold

            if total < reorder_point:
                return "LOW"
            elif total > reorder_point * 2:
                return "HIGH"
            return "NORMAL"

        except Exception as e:
            logger.warning(f"Error assessing inventory for {sector}: {e}")
            return "UNKNOWN"

    async def _assess_sector_demand(
        self,
        sector: str,
        destination_profiles: Dict[str, Any],
    ) -> str:
        """
        Assess demand level based on store profiles in the sector.

        Returns: "LOW", "NORMAL", or "HIGH"
        """
        try:
            stores = destination_profiles.get("stores", [])
            if not stores:
                return "NORMAL"

            # Average the daily demand from stores
            demands = [s.get("average_daily_demand", 0) for s in stores]
            avg_demand = sum(demands) / len(demands) if demands else 0

            if avg_demand > 500:
                return "HIGH"
            elif avg_demand < 100:
                return "LOW"
            return "NORMAL"

        except Exception as e:
            logger.warning(f"Error assessing demand for {sector}: {e}")
            return "UNKNOWN"

    async def _get_driver_availability(self, sector: str) -> Dict[str, Any]:
        """Get driver availability metrics for the sector."""
        try:
            drivers = await self.profile_service.discover_drivers()
            return {
                "total_available": len(drivers),
                "emergency_ready": sum(1 for d in drivers if d.get("emergency_ready")),
                "avg_capacity_kg": sum(d.get("max_load_kg", 0) for d in drivers) / len(drivers) if drivers else 0,
            }

        except Exception as e:
            logger.warning(f"Error getting driver availability: {e}")
            return {}

    async def _get_store_capacity(self, sector: str) -> Dict[str, Any]:
        """Get store capacity metrics for the sector."""
        try:
            stores = await self.profile_service.discover_stores()
            return {
                "total_stores": len(stores),
                "accepting_emergency": sum(1 for s in stores if s.get("accepts_emergency_deliveries")),
                "total_cold_storage_capacity": sum(s.get("cold_storage_capacity", 0) for s in stores),
            }

        except Exception as e:
            logger.warning(f"Error getting store capacity: {e}")
            return {}

    async def _get_farmer_surplus(self, sector: str) -> Dict[str, Any]:
        """Get farmer surplus/supply metrics for the sector."""
        try:
            farmers = await self.profile_service.discover_farmers()
            return {
                "total_farmers": len(farmers),
                "can_self_deliver": sum(1 for f in farmers if f.get("can_self_deliver")),
                "total_available_qty": sum(f.get("available_quantity", 0) for f in farmers),
                "avg_trust_score": (
                    sum((f.get("user_profile") or {}).get("trust_score", 0) for f in farmers) / len(farmers)
                    if farmers else 0
                ),
            }

        except Exception as e:
            logger.warning(f"Error getting farmer surplus: {e}")
            return {}
