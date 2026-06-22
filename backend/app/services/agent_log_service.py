"""
AgentLogService — logs agent decisions, actions, and outcomes for audit and learning.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.agent_log import AgentLog, AgentLogStatus
from app.schemas.agent_log import AgentLogCreate
from app.services.log_service import LogService


class AgentLogService(LogService):
    """
    Extended LogService for agent-specific logging.

    Provides helper methods for agents to log their decisions with
    relevant metadata (shipment, incident, confidence, etc).
    """

    def __init__(self, db: Any) -> None:
        super().__init__(db)

    async def get_recent(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> List[AgentLog]:
        """Get recent agent logs."""
        return await self.get_logs(limit=limit, since=since)

    async def create_log(
        self,
        agent_name: str,
        shipment_id: Optional[str] = None,
        decision: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        status: str = "success",
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> AgentLog:
        """
        Create an agent log entry with orchestrator context.

        Args:
            agent_name: Name of the agent (e.g., "LogisticsAgent", "SourcingAgent")
            shipment_id: ID of the shipment being processed (if applicable)
            decision: Type of decision made (e.g., "REROUTE", "ALLOCATE_SUPPLY")
            payload: Decision payload/details
            confidence: Confidence score (0.0-1.0)
            status: Log status ("success", "partial", "failed")
            message: Human-readable message
            result: Execution result

        Returns:
            Created AgentLog object
        """
        # Determine agent type from agent name
        agent_type = self._determine_agent_type(agent_name)

        # Build message if not provided
        if not message:
            message = f"{agent_name} decided: {decision}" if decision else f"{agent_name} executed"

        # Create the log payload
        log_payload = AgentLogCreate(
            agent_name=agent_name,
            agent_type=agent_type,
            action_type=decision or "UNKNOWN",
            status=status,
            message=message,
            payload=payload or {},
            result=result or {},
            confidence=confidence,
        )

        # Use parent class method to create and broadcast
        return await super().create_log(log_payload)

    async def create_orchestrator_log(
        self,
        orchestrator_action: str,
        sector: str,
        agents_invoked: List[str],
        shipments_processed: int,
        success_count: int,
        heuristics_applied: Optional[List[str]] = None,
    ) -> AgentLog:
        """
        Log a high-level orchestrator action (sector-wide execution).

        Args:
            orchestrator_action: Action type (e.g., "SECTOR_REROUTE")
            sector: Sector that was processed
            agents_invoked: List of agent names invoked
            shipments_processed: Total shipments processed
            success_count: Shipments with successful actions
            heuristics_applied: List of heuristics that were applied

        Returns:
            Created AgentLog object
        """
        success_rate = (
            (success_count / shipments_processed * 100)
            if shipments_processed > 0
            else 0
        )

        return await self.create_log(
            agent_name="AgentOrchestrator",
            decision=orchestrator_action,
            message=f"Orchestrator processed {shipments_processed} shipments in sector {sector}",
            payload={
                "sector": sector,
                "agents_invoked": agents_invoked,
                "shipments_processed": shipments_processed,
                "success_rate_pct": success_rate,
                "heuristics_applied": heuristics_applied or [],
            },
            confidence=success_rate / 100,
            status="success" if success_count > 0 else "partial",
        )

    async def get_agent_logs_by_shipment(
        self,
        shipment_id: str,
    ) -> List[AgentLog]:
        """Get all agent logs related to a specific shipment."""
        logs = await self.get_logs()
        return [
            log for log in logs
            if log.payload and log.payload.get("shipment_id") == shipment_id
        ]

    async def get_agent_logs_by_sector(
        self,
        sector: str,
        limit: int = 100,
    ) -> List[AgentLog]:
        """Get all agent logs for a specific sector."""
        logs = await self.get_logs(limit=limit)
        return [
            log for log in logs
            if log.payload and log.payload.get("sector") == sector
        ]

    def _determine_agent_type(self, agent_name: str) -> str:
        """Determine agent type from agent name."""
        name_lower = agent_name.lower()

        if "logistics" in name_lower:
            return "LOGISTICS"
        elif "sourcing" in name_lower:
            return "SOURCING"
        elif "negotiation" in name_lower:
            return "NEGOTIATION"
        elif "orchestrator" in name_lower:
            return "ORCHESTRATOR"

        return "UNKNOWN"

