"""
SourcingAgent — allocates surplus supply to high-demand nodes using farmer and store profiles.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent
from app.database.supabase_client import supabase_admin

logger = logging.getLogger(__name__)


class SourcingAgent(BaseAgent):
    """Identifies and reallocates surplus inventory using farmer and store profile data.
    
    Uses farmer profiles (crops_produced, available_quantity, storage_availability, can_self_deliver),
    store profiles (inventory_categories, average_daily_demand, current_suppliers, cold_storage_capacity),
    and trust scores to optimally match supply with demand.
    """

    def __init__(self) -> None:
        super().__init__(name="Sourcing Agent")
        self.client = supabase_admin

    async def perceive(self, context: AgentContext) -> Dict[str, Any]:
        """Gather farmer, store, and inventory profile data for supply matching."""
        try:
            metadata = context.metadata or {}
            sector = context.sector

            # Fetch available farmers and their surplus inventory
            available_farmers = await self._fetch_available_farmers(sector)

            # Fetch stores with demand
            demand_stores = await self._fetch_demand_stores(sector)

            # Get inventory levels
            inventory_data = metadata.get("inventory_status", "NORMAL")

            return {
                "sector": sector,
                "metadata": metadata,
                "available_farmers": available_farmers,
                "demand_stores": demand_stores,
                "inventory_level": self._inventory_level_to_percentage(inventory_data),
                "farmer_surplus": metadata.get("farmer_surplus", {}),
                "store_capacity": metadata.get("store_capacity", {}),
            }

        except Exception as e:
            logger.exception(f"Error in SourcingAgent.perceive: {e}")
            return {"error": str(e), "sector": context.sector}

    async def decide(self, perception: Dict[str, Any]) -> AgentAction:
        """Decide sourcing allocation based on farmer supply and store demand profiles."""
        
        try:
            inventory_level = perception.get("inventory_level", 50)
            available_farmers = perception.get("available_farmers", [])
            demand_stores = perception.get("demand_stores", [])

            # Decision logic
            action_type = "ALLOCATE_SURPLUS" if inventory_level > 80 else "REQUEST_RESUPPLY"

            if action_type == "ALLOCATE_SURPLUS":
                # Match farmers with high supply to stores with high demand
                farmer_store_pairs = self._match_farmers_to_stores(
                    farmers=available_farmers,
                    stores=demand_stores,
                )

                confidence = 0.88 if farmer_store_pairs else 0.60

                payload = {
                    "source_warehouse": self._select_warehouse(perception.get("sector", "")),
                    "target_sector": perception["sector"],
                    "inventory_level": inventory_level,
                    "action": "ALLOCATE_SURPLUS",
                    "farmer_matches": farmer_store_pairs,
                    "farmer_matching": {
                        "required_crops": ["Rice", "Wheat", "Vegetables", "Fruits"],
                        "min_quantity_kg": 250,
                        "trust_score_threshold": 3.0,
                        "prefer_self_deliver": True,
                    },
                    "store_matching": {
                        "demand_categories": ["Staples", "Produce", "Perishables"],
                        "cold_storage_required": False,
                        "min_daily_demand": 100,
                    },
                    "total_pairs": len(farmer_store_pairs),
                    "total_available_qty": perception.get("farmer_surplus", {}).get("total_available_qty", 0),
                }

            else:
                # REQUEST_RESUPPLY: find farmers with surplus to restock
                high_supply_farmers = [
                    f for f in available_farmers
                    if f.get("available_quantity", 0) >= 500
                ]

                confidence = 0.85 if high_supply_farmers else 0.50

                payload = {
                    "action": "REQUEST_RESUPPLY",
                    "target_sector": perception["sector"],
                    "inventory_level": inventory_level,
                    "critical_farmers": high_supply_farmers[:5],  # Top 5 farmers by supply
                    "sourcing_priority": [
                        "high_trust_score",
                        "nearby_location",
                        "can_self_deliver",
                        "cold_storage_available"
                    ],
                    "required_crops": ["Rice", "Wheat", "Vegetables"],
                    "min_resupply_qty": 1000,
                    "total_farmer_capacity": perception.get("farmer_surplus", {}).get("total_available_qty", 0),
                }

            return AgentAction(
                agent_name=self.name,
                action_type=action_type,
                payload=payload,
                confidence=confidence,
            )

        except Exception as e:
            logger.exception(f"Error in SourcingAgent.decide: {e}")
            return AgentAction(
                agent_name=self.name,
                action_type="ERROR",
                payload={"error": str(e)},
                confidence=0.0,
            )

    async def act(self, action: AgentAction) -> Dict[str, Any]:
        """Execute the sourcing allocation.
        
        Returns execution results with farmer-store assignments.
        """
        return {
            "agent": self.name,
            "action": action.action_type,
            "details": action.payload,
            "confidence": action.confidence,
            "status": "executed"
        }

    async def _fetch_available_farmers(self, sector: str) -> List[Dict[str, Any]]:
        """Fetch all available farmers in the sector from Supabase."""
        try:
            result = self.client.table("farmer_profiles").select(
                "id, farmer_name, crops_produced, available_quantity, "
                "storage_availability, can_self_deliver, trust_score, farm_location"
            ).ilike("farm_location", f"%{sector}%").execute()

            farmers = result.data if result.data else []
            logger.info(f"Fetched {len(farmers)} available farmers in sector {sector}")
            return farmers

        except Exception as e:
            logger.warning(f"Error fetching farmers for sector {sector}: {e}")
            return []

    async def _fetch_demand_stores(self, sector: str) -> List[Dict[str, Any]]:
        """Fetch stores with demand in the sector."""
        try:
            result = self.client.table("store_profiles").select(
                "id, store_name, inventory_categories, average_daily_demand, "
                "cold_storage_capacity, current_suppliers, store_location"
            ).ilike("store_location", f"%{sector}%").execute()

            stores = result.data if result.data else []
            logger.info(f"Fetched {len(stores)} demand stores in sector {sector}")
            return stores

        except Exception as e:
            logger.warning(f"Error fetching demand stores for sector {sector}: {e}")
            return []

    def _match_farmers_to_stores(
        self,
        farmers: List[Dict[str, Any]],
        stores: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Match farmers with surplus to stores with demand.
        
        Scoring:
        1. Crop type match (farmer crops vs store categories)
        2. Quantity match (farmer available vs store daily demand)
        3. Trust score (farmer trust_score)
        4. Distance/delivery capability (farmer can_self_deliver)
        """
        pairs = []

        for farmer in farmers:
            if farmer.get("available_quantity", 0) < 250:
                continue  # Skip farmers with insufficient surplus

            best_store = None
            best_score = 0

            for store in stores:
                score = self._compute_match_score(farmer, store)
                if score > best_score:
                    best_score = score
                    best_store = store

            if best_store and best_score > 0.5:  # Threshold for a valid match
                pairs.append({
                    "farmer_id": farmer.get("id"),
                    "farmer_name": farmer.get("farmer_name"),
                    "crops": farmer.get("crops_produced", []),
                    "available_qty_kg": farmer.get("available_quantity", 0),
                    "store_id": best_store.get("id"),
                    "store_name": best_store.get("store_name"),
                    "store_demand": best_store.get("average_daily_demand", 0),
                    "match_score": round(best_score, 2),
                    "self_deliver": farmer.get("can_self_deliver", False),
                    "trust_score": farmer.get("trust_score", 0),
                })

        return pairs

    def _compute_match_score(
        self,
        farmer: Dict[str, Any],
        store: Dict[str, Any],
    ) -> float:
        """
        Compute a match score between farmer and store (0.0 to 1.0).
        
        Factors:
        - Crop type match (30%)
        - Quantity compatibility (40%)
        - Farmer trust score (20%)
        - Self-delivery capability (10%)
        """
        score = 0.0

        # Factor 1: Crop type match
        farmer_crops = set(str(c).lower() for c in (farmer.get("crops_produced") or []))
        store_categories = set(str(c).lower() for c in (store.get("inventory_categories") or []))
        crop_match = len(farmer_crops & store_categories) / max(len(farmer_crops | store_categories), 1)
        score += crop_match * 0.30

        # Factor 2: Quantity compatibility
        available = farmer.get("available_quantity", 0)
        demand = store.get("average_daily_demand", 0)
        qty_match = min(available / max(demand * 3, 1), 1.0)  # 3 days of demand
        score += qty_match * 0.40

        # Factor 3: Farmer trust score
        trust = min(farmer.get("trust_score", 0) / 5.0, 1.0)  # Normalize to 0-1
        score += trust * 0.20

        # Factor 4: Self-delivery capability
        can_deliver = 1.0 if farmer.get("can_self_deliver", False) else 0.5
        score += can_deliver * 0.10

        return score

    def _inventory_level_to_percentage(self, status: str) -> float:
        """Convert inventory status string to percentage."""
        mapping = {
            "LOW": 30,
            "NORMAL": 60,
            "HIGH": 85,
            "UNKNOWN": 50,
        }
        return mapping.get(status.upper(), 50)

    def _select_warehouse(self, sector: str) -> str:
        """Select warehouse based on sector."""
        warehouse_map = {
            "NORTH": "Warehouse Alpha",
            "SOUTH": "Warehouse Bravo",
            "EAST": "Warehouse Charlie",
            "WEST": "Warehouse Delta",
        }
        return warehouse_map.get(sector.upper(), "Central Warehouse")
