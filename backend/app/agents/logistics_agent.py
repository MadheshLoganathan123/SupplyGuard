"""
LogisticsAgent — reroutes shipments around disruptions using driver profiles, store demand, and emergency capabilities.
"""

from typing import Any, Dict

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent


class LogisticsAgent(BaseAgent):
    """Handles dynamic route optimization for active shipments.
    
    Uses driver profiles (vehicle_type, max_load_kg, operating_radius_km, emergency_ready),
    store profiles (average_daily_demand, accepting_emergency_deliveries), and location data
    to optimize routes and prioritize emergency shipments.
    """

    def __init__(self) -> None:
        super().__init__(name="Logistics Agent")

    async def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """Gather shipment, driver, and store profile data for the current sector."""
        return {
            "sector": context.sector,
            "threat_level": context.threat_level,
            "incidents": context.active_incidents,
            "metadata": context.metadata,
            # In production:
            # - Query driver_profiles from DB for available drivers in sector
            # - Query store_profiles for store demand and emergency acceptance
            # - Fetch shipment details with origin/destination
        }

    async def decide(self, perception: Dict[str, Any]) -> AgentAction:
        """Decide reroute based on threat, driver availability, and store constraints."""
        action_type = "REROUTE" if perception["threat_level"] in ("ELEVATED", "CRITICAL") else "MONITOR"
        
        # In production, filter drivers by:
        # - Vehicle capacity (max_load_kg >= shipment weight)
        # - Operating radius (distance to origin <= max_delivery_distance_km)
        # - Availability status (online, available_weekdays match)
        # - Capability flags (emergency_ready if incident is emergency, night_delivery_allowed, flood_zone_access)
        
        # Filter stores by:
        # - Accepting emergency deliveries (if critical)
        # - Cold storage availability (if perishables)
        # - Current demand vs capacity
        
        return AgentAction(
            agent_name=self.name,
            action_type=action_type,
            payload={
                "sector": perception["sector"],
                "reason": f"Threat level is {perception['threat_level']}",
                "alternate_path": "Perimeter Node B bypass",
                "driver_capability_filter": {
                    "min_capacity_kg": 500,
                    "max_radius_km": 50,
                    "emergency_mode": perception["threat_level"] == "CRITICAL",
                    "night_delivery": False
                },
                "store_filter": {
                    "accept_emergency": perception["threat_level"] == "CRITICAL",
                    "check_cold_storage": True,
                }
            },
            confidence=0.92,
        )

    async def act(self, action: AgentAction) -> Dict[str, Any]:
        """Execute the reroute action.
        
        In production:
        - Fetch matching drivers from DB (using driver_profiles.*)
        - Fetch matching stores from DB (using store_profiles.*)
        - Call routing model with constraints
        - Update shipment status via ShipmentService
        """
        return {
            "agent": self.name,
            "action": action.action_type,
            "details": action.payload,
            "confidence": action.confidence,
            "notes": "Profile-aware reroute decision; awaiting backend service integration"
        }
