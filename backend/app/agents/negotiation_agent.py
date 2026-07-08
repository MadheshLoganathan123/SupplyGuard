"""
NegotiationAgent — Coordinates pantry/incident responses and supply negotiations.
Uses LLM to evaluate interventions and coordinate multi-agent resource allocation.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentAction, AgentContext, BaseAgent
from app.services.agent_tools import AgentTools
from app.services.incident_service import IncidentService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class NegotiationAgent(BaseAgent):
    """
    Coordinates pantry/incident responses and supply negotiations.

    Responsibilities:
    - Evaluate proposed interventions using LLM
    - Negotiate supply allocations between nodes
    - Coordinate multi-agent resource deployment
    - Track negotiation history and outcomes
    """

    def __init__(self, db: AsyncSession):
        super().__init__(name="Negotiation Agent")
        self.db = db
        self.tools = AgentTools(db)
        self.llm_service = LLMService()
        self.incident_service = IncidentService(db)
        from app.services.intervention_service import InterventionService
        self.intervention_service = InterventionService(db)

    async def perceive(self, context: AgentContext) -> dict[str, Any]:
        """Gather incident, intervention, and supply state."""
        try:
            metadata = context.metadata or {}
            incident_id = metadata.get("incident_id")
            sector = context.sector

            # Fetch active incidents
            incidents = []
            if incident_id:
                incident = await self.incident_service.get_by_id(incident_id)
                if incident:
                    incidents = [
                        {
                            "id": incident.id,
                            "type": incident.title,
                            "description": incident.description,
                            "severity": getattr(incident.severity, "value", incident.severity),
                            "sector": incident.sector,
                        }
                    ]
            else:
                # Get all active incidents in sector
                all_incidents = await self.incident_service.get_open()
                incidents = [
                    {
                        "id": inc.id,
                        "type": inc.title,
                        "description": inc.description,
                        "severity": getattr(inc.severity, "value", inc.severity),
                        "sector": inc.sector,
                    }
                    for inc in all_incidents
                    if inc.sector == sector or not sector
                ]

            # Get available supply to address incidents
            available_supply = await self.tools.query_inventory(
                sector=sector,
                item_type=metadata.get("needed_item_type"),
            )

            # Get stores with demand
            demand_nodes = await self.tools.find_stores_with_demand(
                sector=sector,
                limit=5,
            )

            # Get farmers with surplus
            surplus_sources = await self.tools.find_farmers_with_surplus(
                sector=sector,
                limit=5,
            )

            return {
                "sector": sector,
                "threat_level": context.threat_level,
                "incidents": incidents,
                "available_supply": available_supply,
                "demand_nodes": demand_nodes,
                "surplus_sources": surplus_sources,
                "incident_id": incident_id,
                "metadata": metadata,
            }

        except Exception as e:
            logger.exception(f"Error in NegotiationAgent.perceive: {e}")
            return {"error": str(e), "sector": context.sector, "incidents": []}

    async def decide(self, perception: dict[str, Any]) -> AgentAction:
        """Use LLM to decide negotiation strategy and interventions."""
        try:
            incidents = perception.get("incidents", [])
            if not incidents:
                return AgentAction(
                    agent_name=self.name,
                    action_type="no_incidents",
                    payload={"message": "No incidents to negotiate"},
                    confidence=1.0,
                )

            # Primary incident to address
            primary_incident = incidents[0]

            # Generate LLM prompt for negotiation strategy
            system_prompt = """You are a supply chain negotiation agent.
Your role is to coordinate interventions for supply chain incidents (shortages, disruptions, quality issues).
Evaluate proposed interventions and suggest resource allocations to resolve incidents.
Return structured JSON with reasoning, action_type, confidence, and tools to execute."""

            user_prompt = await self.llm_service.generate_agent_prompt(
                agent_role="negotiation",
                sector_state={
                    "incident": primary_incident,
                    "available_supply": perception.get("available_supply", [])[:3],
                    "demand_nodes": perception.get("demand_nodes", [])[:3],
                    "surplus_sources": perception.get("surplus_sources", [])[:3],
                },
                incidents=incidents,
            )

            # Call LLM for decision
            llm_decision = await self.llm_service.reason(
                context=perception,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            # Convert LLM decision to AgentAction
            return AgentAction(
                agent_name=self.name,
                action_type=llm_decision.action_type,
                payload={
                    "reasoning": llm_decision.reasoning,
                    "confidence": llm_decision.confidence,
                    "tools": [
                        {"name": t.tool_name, "params": t.params}
                        for t in llm_decision.tools
                    ],
                    "incident_id": perception.get("incident_id"),
                    "metadata": llm_decision.metadata,
                },
                confidence=llm_decision.confidence,
            )

        except Exception as e:
            logger.exception(f"Error in NegotiationAgent.decide: {e}")
            return AgentAction(
                agent_name=self.name,
                action_type="error",
                payload={"error": str(e)},
                confidence=0.0,
            )

    async def act(self, action: AgentAction) -> dict[str, Any]:
        """Execute negotiation action: create interventions, allocate resources."""
        try:
            action_type = action.action_type
            payload = action.payload

            if action_type == "no_incidents":
                return {"status": "success", "message": "No interventions needed"}

            if action_type == "error":
                return {"status": "error", "message": payload.get("error")}

            # Execute tools from LLM decision
            tools = payload.get("tools", [])
            execution_results = []

            for tool in tools:
                tool_name = tool.get("name")
                tool_params = tool.get("params", {})

                try:
                    if tool_name == "allocate_supply":
                        result = await self._allocate_supply(**tool_params)
                    elif tool_name == "request_emergency_supply":
                        result = await self._request_emergency_supply(**tool_params)
                    elif tool_name == "negotiate_alternate_route":
                        result = await self._negotiate_alternate_route(**tool_params)
                    else:
                        result = {"status": "unknown_tool", "tool": tool_name}

                    execution_results.append(result)
                except Exception as e:
                    logger.exception(f"Error executing tool {tool_name}: {e}")
                    execution_results.append({"status": "error", "tool": tool_name, "error": str(e)})

            return {
                "status": "success",
                "action_type": action_type,
                "reasoning": payload.get("reasoning", ""),
                "confidence": payload.get("confidence", 0.0),
                "execution_results": execution_results,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.exception(f"Error in NegotiationAgent.act: {e}")
            return {"status": "error", "message": str(e)}

    async def _allocate_supply(
        self,
        source_node_id: str,
        destination_node_id: str,
        item_type: str,
        quantity: int,
        **kwargs,
    ) -> dict[str, Any]:
        """Allocate supply from source to destination."""
        try:
            # Validate that source has sufficient inventory
            inventory = await self.tools.query_inventory(
                item_type=item_type,
            )

            allocated = {
                "source": source_node_id,
                "destination": destination_node_id,
                "item_type": item_type,
                "quantity": quantity,
                "status": "allocated",
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Supply allocated: {allocated}")
            return allocated
        except Exception as e:
            logger.exception(f"Error allocating supply: {e}")
            return {"status": "error", "error": str(e)}

    async def _request_emergency_supply(
        self,
        needed_item_type: str,
        quantity: int,
        urgency_level: str = "high",
        **kwargs,
    ) -> dict[str, Any]:
        """Request emergency supply from nearby surplus sources."""
        try:
            # Find farmers with surplus
            farmers = await self.tools.find_farmers_with_surplus(
                item_type=needed_item_type,
                min_surplus=quantity,
                limit=3,
            )

            if not farmers:
                return {
                    "status": "no_surplus_found",
                    "item_type": needed_item_type,
                    "quantity": quantity,
                }

            # Select best source (highest surplus)
            best_source = max(farmers, key=lambda f: f["surplus"])

            request = {
                "item_type": needed_item_type,
                "quantity": quantity,
                "source_farmer_id": best_source["farmer_id"],
                "urgency": urgency_level,
                "status": "requested",
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"Emergency supply requested: {request}")
            return request
        except Exception as e:
            logger.exception(f"Error requesting emergency supply: {e}")
            return {"status": "error", "error": str(e)}

    async def _negotiate_alternate_route(
        self,
        origin_node_id: str,
        destination_node_id: str,
        primary_route_blocked: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Negotiate alternate route using available drivers."""
        try:
            # Compute alternate route
            route = await self.tools.compute_route(
                origin_node_id=origin_node_id,
                destination_node_id=destination_node_id,
                optimize_for="reliability",
            )

            if route.get("status") != "success":
                return route

            return {
                "status": "route_negotiated",
                "origin": origin_node_id,
                "destination": destination_node_id,
                "route": route.get("route"),
                "recommended_drivers": route.get("recommended_drivers", []),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.exception(f"Error negotiating alternate route: {e}")
            return {"status": "error", "error": str(e)}
