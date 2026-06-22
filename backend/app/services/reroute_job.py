"""
Reroute Job Service — async background job that orchestrates agent-driven shipment rerouting.

This service:
1. Fetches a shipment to reroute
2. Builds ProfileContext (sector, threat, profiles)
3. Invokes LogisticsAgent for decision-making
4. Applies heuristics to adjust confidence
5. Executes the action (update shipment)
6. Logs all decisions for audit
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.database.session import AsyncSessionLocal
from app.models.shipment import ShipmentStatus
from app.services.shipment_service import ShipmentService

logger = logging.getLogger(__name__)


async def run_reroute_job(
    shipment_id: str,
    incident_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Execute a reroute job for a specific shipment using the agent orchestrator.

    Args:
        shipment_id: ID of the shipment to reroute
        incident_ids: List of active incident IDs (for context)

    Returns:
        Dict with results:
        {
            "shipment_id": str,
            "shipment_code": str,
            "status": str,
            "action_taken": str,
            "confidence": float,
            "logs_created": int,
            "error": str (if any)
        }
    """
    logger.info(f"Starting reroute job for shipment {shipment_id}, incidents: {incident_ids}")

    async with AsyncSessionLocal() as db:
        try:
            # Initialize the orchestrator
            orchestrator = AgentOrchestrator(db)

            # Run the full agent cycle
            result = await orchestrator.run_for_shipment(
                shipment_id=shipment_id,
                incident_ids=incident_ids or [],
            )

            if "error" in result:
                logger.error(f"Orchestration error for shipment {shipment_id}: {result['error']}")
                return {
                    "shipment_id": shipment_id,
                    "status": "error",
                    "error": result["error"],
                }

            # Extract results
            shipment = result.get("shipment")
            actions = result.get("actions", [])
            logs = result.get("logs", [])
            heuristic_adjustments = result.get("heuristic_adjustments", {})

            # Summary
            primary_action = actions[0] if actions else None
            action_type = primary_action.action_type if primary_action else "MONITOR"
            confidence = primary_action.confidence if primary_action else 0.0

            logger.info(
                f"Reroute job complete for shipment {shipment.shipment_code}: "
                f"action={action_type}, confidence={confidence}, logs={len(logs)}"
            )

            await db.commit()

            return {
                "shipment_id": shipment.id,
                "shipment_code": shipment.shipment_code,
                "status": shipment.status.value,
                "action_taken": action_type,
                "confidence": confidence,
                "logs_created": len(logs),
                "heuristics_applied": heuristic_adjustments.get("applied_rules", []),
                "selected_driver": primary_action.payload.get("selected_driver") if primary_action else None,
                "selected_store": primary_action.payload.get("selected_store") if primary_action else None,
            }

        except Exception as e:
            logger.exception(f"Error in reroute job for shipment {shipment_id}: {e}")
            await db.rollback()
            return {
                "shipment_id": shipment_id,
                "status": "error",
                "error": str(e),
            }


async def run_reroute_batch(
    status_filter: str = "IN-TRANSIT",
    sector: Optional[str] = None,
    incident_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Execute reroute jobs for all shipments matching filters.

    Args:
        status_filter: Shipment status to filter (default: IN-TRANSIT)
        sector: Sector to filter (optional)
        incident_ids: List of active incident IDs

    Returns:
        Aggregated results
    """
    logger.info(f"Starting batch reroute job: status={status_filter}, sector={sector}")

    async with AsyncSessionLocal() as db:
        try:
            shipment_service = ShipmentService(db)
            orchestrator = AgentOrchestrator(db)

            # Fetch shipments to process
            if status_filter == "IN-TRANSIT":
                shipments = await shipment_service.get_by_status(ShipmentStatus.IN_TRANSIT)
            else:
                shipments = await shipment_service.get_all(limit=1000)

            # Filter by sector if provided
            if sector:
                shipments = [
                    s for s in shipments
                    if sector.lower() in s.destination.lower()
                ]

            results = []
            for shipment in shipments:
                try:
                    result = await orchestrator.run_for_shipment(
                        shipment_id=shipment.id,
                        incident_ids=incident_ids or [],
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to reroute shipment {shipment.id}: {e}")
                    results.append({
                        "shipment_id": shipment.id,
                        "status": "error",
                        "error": str(e),
                    })

            await db.commit()

            # Summary statistics
            successful = sum(1 for r in results if "error" not in r)
            failed = len(results) - successful
            total_logs = sum(len(r.get("logs", [])) for r in results if "logs" in r)

            logger.info(
                f"Batch reroute complete: {successful} successful, {failed} failed, "
                f"{total_logs} logs created"
            )

            return {
                "batch_status": "complete",
                "shipments_processed": len(results),
                "successful": successful,
                "failed": failed,
                "total_logs": total_logs,
                "results": results,
            }

        except Exception as e:
            logger.exception(f"Error in batch reroute job: {e}")
            return {
                "batch_status": "error",
                "error": str(e),
            }


# Legacy support: synchronous wrapper for existing code
def run_reroute_job_sync(shipment_id: str, incident_ids: Optional[list[str]] = None) -> Dict[str, Any]:
    """Synchronous wrapper for async reroute job (for background tasks)."""
    return asyncio.run(run_reroute_job(shipment_id, incident_ids))
