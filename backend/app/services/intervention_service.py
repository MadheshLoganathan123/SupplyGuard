"""
Intervention Service — handles operator interventions and triggers agent responses.

Flow:
1. Operator creates an intervention (e.g., "Reroute shipment SHP-123 due to flood")
2. Service classifies the intervention (reroute, allocate_supply, negotiate)
3. Service invokes appropriate agents (LogisticsAgent, SourcingAgent, NegotiationAgent)
4. Service captures agent decision/response
5. Service marks intervention as resolved or escalated
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import AgentContext
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.orchestrator import AgentOrchestrator
from app.database.session import AsyncSessionLocal
from app.models.intervention import Intervention
from app.models.shipment import Shipment
from app.schemas.dashboard import InterventionCreate
from app.services.agent_log_service import AgentLogService
from app.services.shipment_service import ShipmentService

logger = logging.getLogger(__name__)


class InterventionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.shipment_service = ShipmentService(db)
        self.agent_log_service = AgentLogService(db)

    async def create(self, payload: InterventionCreate) -> Intervention:
        """Create a new operator intervention."""
        intervention = Intervention(**payload.model_dump())
        self.db.add(intervention)
        await self.db.flush()
        await self.db.refresh(intervention)
        return intervention

    async def get_by_id(self, intervention_id: str) -> Optional[Intervention]:
        """Fetch intervention by ID."""
        result = await self.db.execute(
            select(Intervention).where(Intervention.id == intervention_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str) -> List[Intervention]:
        """Fetch all interventions with a given status."""
        result = await self.db.execute(
            select(Intervention).where(Intervention.status == status)
        )
        return result.scalars().all()

    async def update_status(
        self,
        intervention_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Optional[Intervention]:
        """Update intervention status."""
        intervention = await self.get_by_id(intervention_id)
        if not intervention:
            return None

        intervention.status = status
        if notes:
            intervention.notes = notes

        await self.db.flush()
        await self.db.refresh(intervention)
        return intervention


async def process_intervention(
    intervention_id: str,
) -> Dict[str, Any]:
    """
    Process an operator intervention through the agent system.

    Flow:
    1. Fetch intervention text
    2. Classify intervention type (reroute, allocate_supply, negotiate)
    3. Extract shipment/node IDs from text
    4. Invoke appropriate agents
    5. Log agent response
    6. Update intervention status

    Returns:
        Dict with:
        - intervention_id
        - status: "resolved" or "escalated"
        - agent_response: Agent's decision/action
        - agent_logs: Logs created by agents
    """
    logger.info(f"Processing intervention {intervention_id}")

    async with AsyncSessionLocal() as db:
        try:
            svc = InterventionService(db)
            intervention = await svc.get_by_id(intervention_id)

            if not intervention:
                logger.warning(f"Intervention {intervention_id} not found")
                return {"error": "Intervention not found"}

            logger.info(f"Intervention text: {intervention.text}")

            # Step 1: Classify intervention type
            intervention_type = _classify_intervention(intervention.text)
            logger.info(f"Classified as: {intervention_type}")

            # Step 2: Extract shipment/node IDs
            shipment_ids = _extract_shipment_ids(intervention.text)
            logger.info(f"Extracted shipment IDs: {shipment_ids}")

            # Step 3: Invoke agents
            orchestrator = AgentOrchestrator(db)
            agent_responses = []

            if intervention_type == "REROUTE" and shipment_ids:
                for shipment_id in shipment_ids[:1]:  # Process first shipment
                    response = await orchestrator.run_for_shipment(
                        shipment_id=shipment_id,
                        incident_ids=[],
                    )
                    agent_responses.append(response)

            elif intervention_type == "ALLOCATE_SUPPLY":
                response = await orchestrator.run_for_sector(
                    sector=_extract_sector(intervention.text) or "CENTRAL",
                    threat_level="NORMAL",
                    incident_ids=[],
                )
                agent_responses.append(response)

            elif intervention_type == "NEGOTIATE":
                negotiation_agent = NegotiationAgent(db)
                context = AgentContext(
                    sector=_extract_sector(intervention.text) or "CENTRAL",
                    threat_level="ELEVATED",
                    active_incidents=[],
                    metadata={"intervention_id": intervention.id, "intervention_text": intervention.text},
                )
                perception = await negotiation_agent.perceive(context)
                action = await negotiation_agent.decide(perception)
                execution = await negotiation_agent.act(action)
                await svc.agent_log_service.create_log(
                    agent_name="NegotiationAgent",
                    decision=action.action_type.upper(),
                    payload=action.payload,
                    result=execution,
                    confidence=action.confidence,
                    message=f"Negotiation agent responded to intervention {intervention.id}",
                )
                agent_responses.append({
                    "action": action.action_type,
                    "confidence": action.confidence,
                    "payload": action.payload,
                    "execution": execution,
                })

            # Step 4: Update intervention status based on response
            response_summary = agent_responses[0] if agent_responses else {}
            if "error" not in response_summary:
                await svc.update_status(
                    intervention_id=intervention_id,
                    status="resolved",
                    notes=f"Agent response: {response_summary.get('action', 'NONE')}",
                )
                result_status = "resolved"
            else:
                await svc.update_status(
                    intervention_id=intervention_id,
                    status="escalated",
                    notes=f"Agent could not resolve: {response_summary.get('error', 'Unknown error')}",
                )
                result_status = "escalated"

            await db.commit()

            return {
                "intervention_id": intervention_id,
                "status": result_status,
                "intervention_type": intervention_type,
                "shipments_processed": len(shipment_ids),
                "agent_responses": agent_responses,
            }

        except Exception as e:
            logger.exception(f"Error processing intervention {intervention_id}: {e}")
            await db.rollback()
            return {
                "intervention_id": intervention_id,
                "status": "error",
                "error": str(e),
            }


async def process_intervention_batch(
    status: str = "queued",
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Process a batch of pending interventions.

    Args:
        status: Intervention status to filter (default: "queued")
        limit: Maximum interventions to process

    Returns:
        Aggregated results
    """
    logger.info(f"Processing batch of {limit} interventions with status={status}")

    async with AsyncSessionLocal() as db:
        try:
            svc = InterventionService(db)
            interventions = await svc.get_by_status(status)
            interventions = interventions[:limit]

            results = []
            for intervention in interventions:
                try:
                    result = await process_intervention(intervention.id)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process intervention {intervention.id}: {e}")
                    results.append({
                        "intervention_id": intervention.id,
                        "status": "error",
                        "error": str(e),
                    })

            await db.commit()

            resolved = sum(1 for r in results if r.get("status") == "resolved")
            escalated = sum(1 for r in results if r.get("status") == "escalated")
            errors = sum(1 for r in results if r.get("status") == "error")

            logger.info(f"Batch complete: {resolved} resolved, {escalated} escalated, {errors} errors")

            return {
                "batch_status": "complete",
                "processed": len(results),
                "resolved": resolved,
                "escalated": escalated,
                "errors": errors,
                "results": results,
            }

        except Exception as e:
            logger.exception(f"Error in intervention batch: {e}")
            return {
                "batch_status": "error",
                "error": str(e),
            }


def _classify_intervention(text: str) -> str:
    """
    Classify intervention type from text.

    Returns: "REROUTE", "ALLOCATE_SUPPLY", "NEGOTIATE", or "OTHER"
    """
    text_lower = text.lower()

    if any(word in text_lower for word in ["reroute", "route", "alternate path", "divert"]):
        return "REROUTE"
    elif any(word in text_lower for word in ["allocate", "supply", "resupply", "inventory"]):
        return "ALLOCATE_SUPPLY"
    elif any(word in text_lower for word in ["negotiate", "agree", "deal", "coordinate"]):
        return "NEGOTIATE"

    return "OTHER"


def _extract_shipment_ids(text: str) -> List[str]:
    """Extract shipment IDs from intervention text (e.g., 'SHP-123', 'shipment-456')."""
    import re

    # Pattern: SHP-xxx or SHIPMENT-xxx
    pattern = r"(SHP-\d+|SHIPMENT-\d+|shp-\d+)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [m.upper() for m in matches]


def _extract_sector(text: str) -> Optional[str]:
    """Extract sector name from intervention text (e.g., 'North', 'East')."""
    sectors = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]
    text_upper = text.upper()

    for sector in sectors:
        if sector in text_upper:
            return sector

    return None
