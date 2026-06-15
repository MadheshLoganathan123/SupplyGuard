"""
SourcingAgent — allocates surplus supply to high-demand nodes using farmer and store profiles.
"""

from typing import Any, Dict

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent


class SourcingAgent(BaseAgent):
    """Identifies and reallocates surplus inventory using farmer and store profile data.
    
    Uses farmer profiles (crops_produced, available_quantity, storage_availability, can_self_deliver),
    store profiles (inventory_categories, average_daily_demand, current_suppliers, cold_storage_capacity),
    and trust scores to optimally match supply with demand.
    """

    def __init__(self) -> None:
        super().__init__(name="Sourcing Agent")

    async def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """Gather farmer, store, and inventory profile data for supply matching."""
        return {
            "sector": context.sector,
            "metadata": context.metadata,
            # In production:
            # - Query farmer_profiles for available crops, quantities, and self-delivery capability
            # - Query store_profiles for demand by category and cold storage needs
            # - Compute trust-weighted availability (farmer trust_score vs. store demand reliability)
            # - Match crop types with store inventory_categories
        }

    async def decide(self, perception: Dict[str, Any]) -> AgentAction:
        """Decide sourcing allocation based on farmer supply and store demand profiles."""
        inventory = perception["metadata"].get("inventory_level", 50)
        action_type = "ALLOCATE_SURPLUS" if inventory > 80 else "REQUEST_RESUPPLY"
        
        # In production, match:
        # - Farmer crops_produced against store inventory_categories
        # - Farmer available_quantity against store average_daily_demand
        # - Farmer can_self_deliver to bypass driver if needed
        # - Farmer storage_availability against store cold_storage_capacity
        # - Trust scores: prioritize reliable farmers (trust_score > threshold)
        # - Delivery distance: farmer max_delivery_distance_km >= distance to store
        
        return AgentAction(
            agent_name=self.name,
            action_type=action_type,
            payload={
                "source_warehouse": "Warehouse Delta",
                "target_sector": perception["sector"],
                "inventory_level": inventory,
                "farmer_matching": {
                    "required_crops": ["Rice", "Wheat", "Vegetables"],
                    "min_quantity_kg": 500,
                    "trust_score_threshold": 3.5,
                    "prefer_self_deliver": False,
                },
                "store_matching": {
                    "demand_categories": ["Staples", "Produce"],
                    "cold_storage_required": False,
                    "min_daily_demand": 100,
                },
            },
            confidence=0.88,
        )

    async def act(self, action: AgentAction) -> Dict[str, Any]:
        """Execute the sourcing allocation.
        
        In production:
        - Query farmer_profiles matching the crop/quantity criteria
        - Query store_profiles matching the demand criteria
        - Compute optimal farmer-to-store assignments (assignment problem)
        - Call InventoryService to allocate stock
        - Log allocation decision with trust scores and matching rationale
        """
        return {
            "agent": self.name,
            "action": action.action_type,
            "details": action.payload,
            "notes": "Profile-aware sourcing decision; awaiting backend service integration"
        }
