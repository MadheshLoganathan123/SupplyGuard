import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.database.session import AsyncSessionLocal
from app.models.inventory import Inventory
from app.models.supply_node import SupplyNode
from app.models.projection import Projection, ProjectionStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.projection import ProjectionCreate
from app.services.heuristics_service import HeuristicsService

logger = logging.getLogger(__name__)


class ProjectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: ProjectionCreate) -> Projection:
        projection = Projection(
            type="demand",
            input=payload.model_dump(),
            status=ProjectionStatus.QUEUED.value,
        )
        self.db.add(projection)
        await self.db.flush()
        await self.db.refresh(projection)
        return projection

    async def get_by_id(self, projection_id: str) -> Projection | None:
        result = await self.db.execute(
            select(Projection).where(Projection.id == projection_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str) -> list[Projection]:
        result = await self.db.execute(
            select(Projection).where(Projection.status == status)
        )
        return result.scalars().all()


async def run_projection_job(
    projection_id: str,
    use_agent_orchestrator: bool = True,
) -> Dict[str, Any]:
    """
    Execute a demand projection job with optional agent orchestration.

    Args:
        projection_id: ID of the projection to run
        use_agent_orchestrator: Whether to invoke agents for supply reallocation

    Returns:
        Dict with projection results
    """
    logger.info(f"Starting projection job {projection_id}, use_orchestrator={use_agent_orchestrator}")

    async with AsyncSessionLocal() as db:
        try:
            svc = ProjectionService(db)
            projection = await svc.get_by_id(projection_id)

            if not projection:
                logger.warning(f"Projection {projection_id} not found")
                return {"error": "Projection not found"}

            # Mark as running
            projection.status = ProjectionStatus.RUNNING.value
            projection.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Step 1: Compute base projection (demand vs supply)
            base_result = await _compute_base_projection(projection)

            # Step 2: If orchestrator enabled, invoke agents to address supply gaps
            orchestrator_result = None
            if use_agent_orchestrator:
                orchestrator_result = await _run_agent_sourcing(
                    db=db,
                    projection=projection,
                    base_result=base_result,
                )

            # Step 3: Apply heuristics to adjust projections
            heuristic_adjustments = await _apply_projection_heuristics(
                db=db,
                base_result=base_result,
                orchestrator_result=orchestrator_result,
            )

            # Step 4: Finalize projection with results
            final_result = {
                "summary": base_result.get("summary", ""),
                "supply_demand_gap_pct": base_result.get("supply_demand_gap_pct", 0),
                "horizon_days": projection.input.get("horizon_days", 7),
                "nodes_analyzed": base_result.get("nodes_analyzed", 0),
                "agents_invoked": orchestrator_result is not None,
                "agent_actions": orchestrator_result.get("actions", []) if orchestrator_result else [],
                "heuristics_applied": heuristic_adjustments.get("applied_rules", []),
                "adjusted_supply_demand_gap": heuristic_adjustments.get("adjusted_gap_pct", base_result.get("supply_demand_gap_pct", 0)),
            }

            # Update projection
            projection.status = ProjectionStatus.DONE.value
            projection.result = final_result
            projection.finished_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Projection {projection_id} completed successfully")

            return {
                "projection_id": projection_id,
                "status": "complete",
                "result": final_result,
            }

        except Exception as e:
            logger.exception(f"Error in projection job {projection_id}: {e}")

            async with AsyncSessionLocal() as db2:
                svc = ProjectionService(db2)
                proj = await svc.get_by_id(projection_id)
                if proj:
                    proj.status = ProjectionStatus.FAILED.value
                    proj.result = {"error": str(e)}
                    proj.finished_at = datetime.now(timezone.utc)
                    await db2.commit()

            return {
                "projection_id": projection_id,
                "status": "error",
                "error": str(e),
            }


async def _compute_base_projection(projection: Projection) -> Dict[str, Any]:
    """
    Compute baseline demand vs supply projection using real inventory data.
    """
    node_ids = projection.input.get("node_ids", [])
    horizon_days = projection.input.get("horizon_days", 7)
    logger.info(f"Computing base projection for {len(node_ids)} nodes, horizon={horizon_days}d")

    async with AsyncSessionLocal() as db:
        # Total inventory stock across relevant nodes
        stock_q = select(func.coalesce(func.sum(Inventory.quantity), 0))
        if node_ids:
            stock_q = stock_q.where(Inventory.node_id.in_(node_ids))
        total_stock = (await db.scalar(stock_q)) or 0

        # Count active shipments (in-transit = incoming supply)
        ship_q = select(func.count()).select_from(Shipment).where(
            Shipment.status == ShipmentStatus.IN_TRANSIT
        )
        if node_ids:
            ship_q = ship_q.where(Shipment.destination_node_id.in_(node_ids))
        incoming_shipments = (await db.scalar(ship_q)) or 0

        # Average shipment volume per node
        vol_q = select(func.coalesce(func.avg(Shipment.quantity), 0))
        if node_ids:
            vol_q = vol_q.where(Shipment.destination_node_id.in_(node_ids))
        avg_shipment_volume = (await db.scalar(vol_q)) or 0

        # Node count
        if node_ids:
            node_count = len(node_ids)
        else:
            node_count = (await db.scalar(select(func.count()).select_from(SupplyNode))) or 1

        # Supply margin: stock + incoming supply over horizon
        incoming_volume = incoming_shipments * avg_shipment_volume
        total_supply = total_stock + incoming_volume

        # Estimate daily demand per node (placeholder: 100 units/node/day)
        estimated_daily_demand = node_count * 100.0
        total_demand = estimated_daily_demand * horizon_days

        supply_margin = max(1.0, (total_supply / total_demand * 100)) if total_demand > 0 else 100.0
        gap = max(0.0, 100.0 - supply_margin)

        return {
            "summary": (
                f"Projection over {horizon_days}d: stock={total_stock:.0f}u, "
                f"incoming={incoming_volume:.0f}u, demand={total_demand:.0f}u, "
                f"margin={supply_margin:.1f}%."
            ),
            "supply_demand_gap_pct": round(gap, 1),
            "nodes_analyzed": node_count,
            "horizon_days": horizon_days,
            "total_stock": total_stock,
            "incoming_shipments": incoming_shipments,
            "avg_shipment_volume": avg_shipment_volume,
            "estimated_daily_demand": estimated_daily_demand,
        }


async def _run_agent_sourcing(
    db: AsyncSession,
    projection: Projection,
    base_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Invoke the SourcingAgent to address supply gaps identified in the projection.

    Returns:
        Dict with agent actions taken (or None if no action needed)
    """
    gap_pct = base_result.get("supply_demand_gap_pct", 0)

    # Only invoke agent if gap is significant
    if gap_pct < 2.0:
        logger.info(f"Supply gap {gap_pct}% is minimal, skipping agent invocation")
        return None

    logger.info(f"Supply gap {gap_pct}% detected, invoking SourcingAgent")

    try:
        orchestrator = AgentOrchestrator(db)

        # Run sector-wide orchestration with "sourcing focus"
        result = await orchestrator.run_for_sector(
            sector=projection.input.get("sector", "CENTRAL"),
            threat_level="NORMAL",
            incident_ids=projection.input.get("incident_ids", []),
        )

        return result

    except Exception as e:
        logger.warning(f"Error invoking SourcingAgent: {e}")
        return None


async def _apply_projection_heuristics(
    db: AsyncSession,
    base_result: Dict[str, Any],
    orchestrator_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply active heuristics to adjust projection results.

    Heuristics may:
    - Reduce supply gap if high-trust farmers are available
    - Increase confidence if emergency capacity is high
    - Flag for manual review if multiple gaps detected
    """
    logger.info("Applying heuristics to projection results")

    try:
        heuristics_svc = HeuristicsService(db)
        heuristic = await heuristics_svc.get_active()

        if not heuristic:
            return {
                "applied": False,
                "applied_rules": [],
                "adjusted_gap_pct": base_result.get("supply_demand_gap_pct", 0),
            }

        gap_pct = base_result.get("supply_demand_gap_pct", 0)
        applied_rules = []
        adjustment = 0.0

        # Example heuristic rules
        rules = heuristic.payload.get("rules", [])
        for rule in rules:
            rule_name = rule.get("name", "unknown")

            # Rule: High farmer trust score reduces gap
            if rule_name == "high_trust_farmer_boost":
                if orchestrator_result and orchestrator_result.get("shipments_processed", 0) > 0:
                    adjustment -= rule.get("adjustment", 0.5)
                    applied_rules.append(rule_name)

            # Rule: Emergency capacity boost
            elif rule_name == "emergency_capacity_high":
                if gap_pct < 3.0:
                    adjustment -= rule.get("adjustment", 0.2)
                    applied_rules.append(rule_name)

            # Rule: Multiple gaps flag for review
            elif rule_name == "multiple_gaps_alert":
                if gap_pct > 5.0:
                    applied_rules.append(f"{rule_name}:REVIEW_REQUIRED")

        adjusted_gap = max(0.0, gap_pct + adjustment)

        return {
            "applied": True,
            "heuristic_id": heuristic.id,
            "applied_rules": applied_rules,
            "original_gap_pct": gap_pct,
            "adjusted_gap_pct": adjusted_gap,
            "adjustment": adjustment,
        }

    except Exception as e:
        logger.warning(f"Error applying heuristics: {e}")
        return {
            "applied": False,
            "error": str(e),
            "adjusted_gap_pct": base_result.get("supply_demand_gap_pct", 0),
        }


# Synchronous wrapper for background task systems
def run_projection_job_sync(
    projection_id: str,
    use_agent_orchestrator: bool = True,
) -> Dict[str, Any]:
    """Synchronous wrapper for async projection job."""
    return asyncio.run(run_projection_job(projection_id, use_agent_orchestrator))
