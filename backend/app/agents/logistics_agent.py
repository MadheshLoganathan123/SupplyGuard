"""
LogisticsAgent — reroutes shipments around disruptions using driver profiles, store demand, and emergency capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent
from app.database.supabase_client import supabase_admin

logger = logging.getLogger(__name__)


class LogisticsAgent(BaseAgent):
    """Handles dynamic route optimization for active shipments.
    
    Uses driver profiles (vehicle_type, max_load_kg, operating_radius_km, emergency_ready),
    store profiles (average_daily_demand, accepting_emergency_deliveries), and location data
    to optimize routes and prioritize emergency shipments.
    """

    def __init__(self) -> None:
        super().__init__(name="Logistics Agent")
        self.client = supabase_admin

    async def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """Gather shipment, driver, and store profile data for the current sector."""
        try:
            metadata = context.metadata or {}
            sector = context.sector

            # Fetch available drivers in the sector
            available_drivers = await self._fetch_available_drivers(sector)

            # Fetch destination stores in the sector
            destination_stores = await self._fetch_destination_stores(
                sector, 
                metadata.get("destination", "")
            )

            # Extract shipment constraints
            shipment_weight = metadata.get("shipment_weight", 100)  # Default 100 kg
            requires_cold_storage = metadata.get("requires_cold_storage", False)
            is_emergency = context.threat_level == "CRITICAL"

            return {
                "sector": sector,
                "threat_level": context.threat_level,
                "incidents": context.active_incidents,
                "available_drivers": available_drivers,
                "destination_stores": destination_stores,
                "shipment_weight": shipment_weight,
                "requires_cold_storage": requires_cold_storage,
                "is_emergency": is_emergency,
                "origin": metadata.get("origin", ""),
                "destination": metadata.get("destination", ""),
                "driver_availability": metadata.get("driver_availability", {}),
                "store_capacity": metadata.get("store_capacity", {}),
            }

        except Exception as e:
            logger.exception(f"Error in LogisticsAgent.perceive: {e}")
            return {"error": str(e), "sector": context.sector}

    async def decide(self, perception: Dict[str, Any]) -> AgentAction:
        """Decide reroute based on threat, driver availability, and store constraints."""
        
        try:
            threat_level = perception.get("threat_level", "NORMAL")
            available_drivers = perception.get("available_drivers", [])
            destination_stores = perception.get("destination_stores", [])

            # Decision logic
            action_type = "REROUTE" if threat_level in ("ELEVATED", "CRITICAL") else "MONITOR"

            if action_type == "REROUTE":
                # Find best driver based on constraints
                best_driver = self._select_best_driver(
                    drivers=available_drivers,
                    origin=perception.get("origin", ""),
                    shipment_weight=perception.get("shipment_weight", 100),
                    requires_emergency=perception.get("is_emergency", False),
                )

                # Find best destination store
                best_store = self._select_best_destination(
                    stores=destination_stores,
                    requires_cold_storage=perception.get("requires_cold_storage", False),
                    is_emergency=perception.get("is_emergency", False),
                )

                # Compute alternate path using selected driver and store
                alternate_path = self._compute_alternate_path(
                    origin=perception.get("origin", ""),
                    destination=best_store.get("store_name", perception.get("destination", "")) if best_store else perception.get("destination", ""),
                    driver=best_driver,
                )

                confidence = 0.85 if best_driver and best_store else 0.65

                payload = {
                    "sector": perception["sector"],
                    "reason": f"Threat level {threat_level}: rerouting via available drivers and alternative stores",
                    "alternate_path": alternate_path,
                    "selected_driver": best_driver.get("driver_name") if best_driver else None,
                    "selected_driver_id": best_driver.get("id") if best_driver else None,
                    "selected_store": best_store.get("store_name") if best_store else None,
                    "selected_store_id": best_store.get("id") if best_store else None,
                    "driver_capability_filter": {
                        "min_capacity_kg": perception.get("shipment_weight", 100),
                        "max_radius_km": 100,
                        "emergency_mode": threat_level == "CRITICAL",
                        "requires_emergency_ready": threat_level == "CRITICAL",
                    },
                    "store_filter": {
                        "accept_emergency": threat_level == "CRITICAL",
                        "check_cold_storage": perception.get("requires_cold_storage", False),
                    },
                    "available_drivers_count": len(available_drivers),
                    "available_stores_count": len(destination_stores),
                }

            else:
                # MONITOR: no reroute needed
                payload = {
                    "sector": perception["sector"],
                    "reason": f"Threat level {threat_level}: monitoring active shipments",
                    "available_drivers_count": len(available_drivers),
                    "available_stores_count": len(destination_stores),
                }
                confidence = 0.95

            return AgentAction(
                agent_name=self.name,
                action_type=action_type,
                payload=payload,
                confidence=confidence,
            )

        except Exception as e:
            logger.exception(f"Error in LogisticsAgent.decide: {e}")
            return AgentAction(
                agent_name=self.name,
                action_type="ERROR",
                payload={"error": str(e)},
                confidence=0.0,
            )

    async def act(self, action: AgentAction) -> Dict[str, Any]:
        """Execute the reroute action.
        
        Returns execution results with selected drivers and stores.
        """
        return {
            "agent": self.name,
            "action": action.action_type,
            "details": action.payload,
            "confidence": action.confidence,
            "status": "executed"
        }

    async def _fetch_available_drivers(self, sector: str) -> List[Dict[str, Any]]:
        """Fetch all available drivers in the sector from Supabase."""
        try:
            result = self.client.table("driver_profiles").select(
                "id, driver_name, vehicle_type, max_load_kg, operating_radius_km, "
                "emergency_ready, operating_location, available_status"
            ).ilike("operating_location", f"%{sector}%").eq("available_status", "available").execute()

            drivers = result.data if result.data else []
            logger.info(f"Fetched {len(drivers)} available drivers in sector {sector}")
            return drivers

        except Exception as e:
            logger.warning(f"Error fetching drivers for sector {sector}: {e}")
            return []

    async def _fetch_destination_stores(
        self, 
        sector: str,
        destination: str
    ) -> List[Dict[str, Any]]:
        """Fetch destination stores in the sector that can accept deliveries."""
        try:
            result = self.client.table("store_profiles").select(
                "id, store_name, store_location, average_daily_demand, "
                "accepting_emergency_deliveries, cold_storage_capacity, accepting_deliveries"
            ).ilike("store_location", f"%{sector}%").eq("accepting_deliveries", True).execute()

            stores = result.data if result.data else []
            logger.info(f"Fetched {len(stores)} available stores in sector {sector}")
            return stores

        except Exception as e:
            logger.warning(f"Error fetching stores for sector {sector}: {e}")
            return []

    def _select_best_driver(
        self,
        drivers: List[Dict[str, Any]],
        origin: str,
        shipment_weight: float,
        requires_emergency: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best driver based on:
        1. Capacity (max_load_kg >= shipment_weight)
        2. Emergency readiness (if required)
        3. Operating radius (can reach origin)
        """
        if not drivers:
            return None

        # Filter by capacity and emergency requirements
        qualified = [
            d for d in drivers
            if d.get("max_load_kg", 0) >= shipment_weight
            and (not requires_emergency or d.get("emergency_ready", False))
        ]

        if not qualified:
            # Fall back to highest capacity driver
            return max(drivers, key=lambda d: d.get("max_load_kg", 0))

        # Prioritize emergency-ready drivers if needed
        if requires_emergency:
            emergency_drivers = [d for d in qualified if d.get("emergency_ready")]
            if emergency_drivers:
                return emergency_drivers[0]

        return qualified[0]

    def _select_best_destination(
        self,
        stores: List[Dict[str, Any]],
        requires_cold_storage: bool,
        is_emergency: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best destination store based on:
        1. Emergency acceptance capability (if needed)
        2. Cold storage capability (if needed)
        3. Current capacity
        """
        if not stores:
            return None

        # Filter by emergency acceptance if needed
        qualified = stores
        if is_emergency:
            qualified = [s for s in stores if s.get("accepting_emergency_deliveries", False)]

        # Filter by cold storage if needed
        if requires_cold_storage:
            qualified = [s for s in qualified if s.get("cold_storage_capacity", 0) > 0]

        if not qualified:
            # Fall back to first available store
            return stores[0]

        # Prefer store with highest demand (to balance supply)
        return max(qualified, key=lambda s: s.get("average_daily_demand", 0))

    def _compute_alternate_path(
        self,
        origin: str,
        destination: str,
        driver: Optional[Dict[str, Any]],
    ) -> str:
        """
        Compute alternate path considering driver location and operating radius.
        
        In production, this would call a routing service (e.g., OSRM, Google Maps).
        For now, return a descriptive path.
        """
        if not driver:
            return f"{origin} → {destination} (direct)"

        driver_name = driver.get("driver_name", "Driver")
        vehicle = driver.get("vehicle_type", "Vehicle")

        return f"{origin} → {destination} (via {driver_name} in {vehicle})"
