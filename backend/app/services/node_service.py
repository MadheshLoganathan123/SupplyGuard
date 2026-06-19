from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supply_node import SupplyNode
from app.models.telemetry import TelemetryMessage
from app.schemas.node import (
    NetworkMetrics,
    NodeConnection,
    NodeDetail,
    NodeListResponse,
    NodeStatusCounts,
    NodeSummary,
)
from app.services.telemetry_service import TelemetryService


class NodeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_status_counts(self) -> NodeStatusCounts:
        rows = await self.db.execute(
            select(SupplyNode.status, func.count())
            .group_by(SupplyNode.status)
        )
        counts = {status: count for status, count in rows.all()}
        return NodeStatusCounts(
            operational=counts.get("OPERATIONAL", 0),
            at_risk=counts.get("AT_RISK", 0),
            blocked=counts.get("BLOCKED", 0),
            inactive=counts.get("INACTIVE", 0),
        )

    async def get_network_metrics(self) -> NetworkMetrics:
        open_risk = await self.db.scalar(
            select(func.count()).where(SupplyNode.status == "AT_RISK")
        )
        blocked = await self.db.scalar(
            select(func.count()).where(SupplyNode.status == "BLOCKED")
        )
        gap = min(15.0, 2.0 + (open_risk or 0) * 0.15 + (blocked or 0) * 0.4)
        return NetworkMetrics(
            latency_ms=20 + (open_risk or 0) * 0.3,
            negotiation_success_pct=max(90.0, 99.0 - (blocked or 0) * 0.2),
            supply_demand_gap_pct=round(gap, 1),
        )

    async def list_nodes(self, limit: int = 200) -> NodeListResponse:
        result = await self.db.execute(
            select(SupplyNode).order_by(SupplyNode.position_index).limit(limit)
        )
        nodes = list(result.scalars().all())
        return NodeListResponse(
            status_counts=await self.get_status_counts(),
            metrics=await self.get_network_metrics(),
            nodes=[NodeSummary.model_validate(n) for n in nodes],
        )

    async def get_by_id(self, node_id: str) -> Optional[SupplyNode]:
        result = await self.db.execute(
            select(SupplyNode).where(SupplyNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_detail(self, node_id: str) -> Optional[NodeDetail]:
        node = await self.get_by_id(node_id)
        if not node:
            return None

        telemetry_svc = TelemetryService(self.db)
        recent = await telemetry_svc.get_recent(limit=10, node_id=node_id)

        connections = [
            NodeConnection(**c) for c in (node.connections or [])
        ]

        return NodeDetail(
            id=node.id,
            name=node.name,
            node_type=node.node_type,
            status=node.status,
            agent_name=node.agent_name,
            image_url=node.image_url,
            inventory_label=node.inventory_label,
            threat_level=node.threat_level,
            throughput=node.throughput,
            position_index=node.position_index,
            inventory_level=float(node.inventory_level) if node.inventory_level is not None else None,
            sector=node.sector,
            connections=connections,
            recent_telemetry=[
                {
                    "id": t.id,
                    "type": t.type,
                    "payload": t.payload,
                    "created_at": t.created_at.isoformat(),
                }
                for t in recent
            ],
        )

    async def get_by_name(self, name: str) -> Optional[SupplyNode]:
        result = await self.db.execute(
            select(SupplyNode).where(SupplyNode.name == name)
        )
        return result.scalar_one_or_none()
