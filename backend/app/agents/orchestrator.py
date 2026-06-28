"""
AgentOrchestrator — manages the perception → decision → action cycle for all agents.
Coordinates ProfileContextService to build rich context, applies heuristics, and logs decisions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent
from app.agents.logistics_agent import LogisticsAgent
from app.agents.sourcing_agent import SourcingAgent
from app.models.agent_log import AgentLog
from app.models.shipment import Shipment, ShipmentStatus
from app.services.agent_log_service import AgentLogService
from app.services.agent_service import AgentService
from app.services.heuristics_service import HeuristicsService
from app.services.profile_context_service import ProfileContextService
from app.services.shipment_service import ShipmentService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for agentic decision-making in SupplyGuard.

    Responsibilities:
    1. Gather shipments and incidents (perceive)
    2. Build rich ProfileContext (sector, threat_level, profiles)
    3. Invoke agents (LogisticsAgent, SourcingAgent)
    4. Apply active heuristics to agent decisions
    5. Execute actions (update shipments, log decisions)
    6. Persist logs for audit & operator review
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.shipment_service = ShipmentService(db)
        self.agent_service = AgentService(db)
        self.heuristics_service = HeuristicsService(db)
        self.log_service = AgentLogService(db)
        self.profile_context = ProfileContextService(db)
        self.agents: Dict[str, BaseAgent] = {
            "logistics": LogisticsAgent(),
            "sourcing": SourcingAgent(),
        }

    async def run_for_shipment(
        self,
        shipment_id: str,
        incident_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full agent cycle for a single shipment.

        Args:
            shipment_id: ID of the shipment to process
            incident_ids: List of active incident IDs (for context)

        Returns:
            Dict containing:
            - shipment: Updated shipment object
            - logs: List of AgentLog entries created
            - actions: List of AgentAction objects executed
            - heuristic_adjustments: Heuristic scoring applied
        """
        try:
            # Step 1: Fetch shipment and build context
            shipment = await self.shipment_service.get_by_id(shipment_id)
            if not shipment:
                logger.warning(f"Shipment {shipment_id} not found.")
                return {"error": "Shipment not found"}

            logger.info(f"Starting orchestration for shipment {shipment.shipment_code}")

            # Build profile context
            context = await self.profile_context.build_context(
                shipment=shipment,
                incident_ids=incident_ids or [],
            )

            # Step 2: Invoke agents in sequence
            actions = []
            logs = []

            # Logistics Agent: decide on rerouting
            if context.threat_level in ("ELEVATED", "CRITICAL"):
                logistics_action = await self._run_agent(
                    agent_name="logistics",
                    context=context,
                )
                actions.append(logistics_action)

                # Log the decision
                log = await self.log_service.create_log(
                    agent_name="LogisticsAgent",
                    shipment_id=shipment_id,
                    decision="REROUTE",
                    payload=logistics_action.payload,
                    confidence=logistics_action.confidence,
                )
                logs.append(log)

            # Sourcing Agent: decide on supply allocation
            # (triggered if demand is high or supply is constrained)
            if context.inventory_status == "LOW" or context.sector_demand_level == "HIGH":
                sourcing_action = await self._run_agent(
                    agent_name="sourcing",
                    context=context,
                )
                actions.append(sourcing_action)

                log = await self.log_service.create_log(
                    agent_name="SourcingAgent",
                    shipment_id=shipment_id,
                    decision="ALLOCATE_SUPPLY",
                    payload=sourcing_action.payload,
                    confidence=sourcing_action.confidence,
                )
                logs.append(log)

            # Step 3: Apply active heuristics to adjust decision confidence/payload
            heuristic_adjustments = await self._apply_heuristics(
                actions=actions,
                context=context,
            )

            # Step 4: Execute the primary action (if any)
            if actions:
                primary_action = actions[0]  # Logistics has priority
                shipment = await self._execute_action(
                    shipment=shipment,
                    action=primary_action,
                    heuristic_adjustments=heuristic_adjustments,
                )

            await self.db.commit()

            logger.info(
                f"Orchestration complete for shipment {shipment.shipment_code}. "
                f"Actions: {len(actions)}, Logs: {len(logs)}"
            )

            return {
                "shipment": shipment,
                "actions": actions,
                "logs": logs,
                "heuristic_adjustments": heuristic_adjustments,
            }

        except Exception as e:
            logger.exception(f"Error during orchestration for shipment {shipment_id}: {e}")
            await self.db.rollback()
            return {"error": str(e)}

    async def run_for_sector(
        self,
        sector: str,
        threat_level: str = "NORMAL",
        incident_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute agent cycle for all active shipments in a sector.

        Args:
            sector: Sector identifier
            threat_level: Current threat level (NORMAL, ELEVATED, CRITICAL)
            incident_ids: List of active incident IDs

        Returns:
            Aggregated results for all shipments processed
        """
        try:
            logger.info(f"Starting orchestration for sector {sector} at threat level {threat_level}")

            # Fetch all in-transit shipments in the sector
            # (simplified; in production, add sector filtering to ShipmentService)
            shipments = await self.shipment_service.get_by_status(ShipmentStatus.IN_TRANSIT)
            if sector and sector != "*":
                shipments = [
                    shipment for shipment in shipments
                    if sector.lower() in (shipment.destination or "").lower()
                    or sector.lower() in (shipment.origin or "").lower()
                ]

            effective_incident_ids = incident_ids or []
            if threat_level != "NORMAL" and not effective_incident_ids:
                effective_incident_ids = [f"manual-{threat_level.lower()}"]

            results = []
            for shipment in shipments:
                result = await self.run_for_shipment(
                    shipment_id=shipment.id,
                    incident_ids=effective_incident_ids,
                )
                results.append(result)

            return {
                "sector": sector,
                "threat_level": threat_level,
                "shipments_processed": len(results),
                "results": results,
            }

        except Exception as e:
            logger.exception(f"Error during sector orchestration for {sector}: {e}")
            return {"error": str(e)}

    async def _run_agent(
        self,
        agent_name: str,
        context: AgentContext,
    ) -> AgentAction:
        """
        Execute a single agent's perception → decide cycle.

        Args:
            agent_name: Name of the agent (e.g., 'logistics', 'sourcing')
            context: AgentContext with sector, threat_level, incidents, metadata

        Returns:
            AgentAction object
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        # Run full cycle: perceive → decide
        perception = await agent.perceive(context)
        action = await agent.decide(perception)

        logger.debug(f"Agent {agent_name} decided: {action.action_type} (confidence={action.confidence})")

        return action

    async def _apply_heuristics(
        self,
        actions: List[AgentAction],
        context: AgentContext,
    ) -> Dict[str, Any]:
        """
        Retrieve active heuristics and adjust action confidence/payload.

        Args:
            actions: List of AgentActions to apply heuristics to
            context: AgentContext (sector, threat_level, incidents)

        Returns:
            Dict of heuristic adjustments:
            {
                "heuristic_id": str,
                "heuristic_name": str,
                "applied_rules": [...],
                "confidence_adjustments": {...},
            }
        """
        try:
            heuristic = await self.heuristics_service.get_active()
            if not heuristic:
                return {"applied": False, "reason": "No active heuristic"}

            adjustments = {
                "heuristic_id": heuristic.id,
                "heuristic_name": heuristic.name,
                "version": heuristic.version,
                "applied_rules": [],
                "confidence_adjustments": {},
            }

            # Example heuristic rules (from heuristic.payload)
            rules = heuristic.payload.get("rules", [])
            for rule in rules:
                rule_name = rule.get("name", "unknown")
                triggers = rule.get("triggers", {})

                # Match rule triggers against context
                if self._rule_matches(triggers, context, actions):
                    adjustment = rule.get("adjustment", {})
                    adjustments["applied_rules"].append(rule_name)
                    adjustments["confidence_adjustments"][rule_name] = adjustment

                    logger.info(f"Applied heuristic rule: {rule_name}")

            return adjustments

        except Exception as e:
            logger.exception(f"Error applying heuristics: {e}")
            return {"error": str(e)}

    def _rule_matches(
        self,
        triggers: Dict[str, Any],
        context: AgentContext,
        actions: List[AgentAction],
    ) -> bool:
        """
        Check if a heuristic rule's triggers match the current context.

        Simple matching logic:
        - threat_level: check if context.threat_level matches
        - incident_count_gt: check if active incidents > threshold
        - action_types: check if any action matches
        """
        threat_level = triggers.get("threat_level")
        if threat_level and context.threat_level != threat_level:
            return False

        incident_count_gt = triggers.get("incident_count_gt")
        if incident_count_gt and len(context.active_incidents) <= incident_count_gt:
            return False

        action_types = triggers.get("action_types")
        if action_types:
            if not any(a.action_type in action_types for a in actions):
                return False

        return True

    async def _execute_action(
        self,
        shipment: Shipment,
        action: AgentAction,
        heuristic_adjustments: Dict[str, Any],
    ) -> Shipment:
        """
        Execute the decided action on a shipment.

        Current implementation:
        - REROUTE: Update shipment status to REROUTED, link to agent, store path
        - ALLOCATE_SUPPLY: Log the decision (actual allocation in InventoryService)

        Args:
            shipment: Shipment to update
            action: AgentAction to execute
            heuristic_adjustments: Adjustments from heuristics (for audit)

        Returns:
            Updated shipment
        """
        try:
            if action.action_type == "REROUTE":
                # Update shipment with new path/route
                shipment.status = ShipmentStatus.REROUTED
                if action.payload.get("alternate_path"):
                    # Store path metadata (in production, add a path column to Shipment)
                    logger.info(
                        f"Shipment {shipment.shipment_code} rerouted via: "
                        f"{action.payload.get('alternate_path')}"
                    )

            elif action.action_type == "ALLOCATE_SUPPLY":
                logger.info(
                    f"Shipment {shipment.shipment_code} flagged for supply allocation: "
                    f"{action.payload.get('source_warehouse')}"
                )

            # Always update the agent_id to link shipment to agent
            agent = await self.agent_service.get_active()
            if agent:
                shipment.agent_id = agent.id

            await self.db.flush()
            await self.db.refresh(shipment)
            return shipment

        except Exception as e:
            logger.exception(f"Error executing action: {e}")
            raise
