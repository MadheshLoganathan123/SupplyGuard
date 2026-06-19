from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import TelemetryMessage
from app.schemas.telemetry import TelemetryCreate
from app.utils.websocket import manager


class TelemetryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recent(self, limit: int = 50, node_id: Optional[str] = None) -> List[TelemetryMessage]:
        query = select(TelemetryMessage).order_by(TelemetryMessage.created_at.desc()).limit(limit)
        if node_id:
            query = query.where(TelemetryMessage.node_id == node_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, payload: TelemetryCreate) -> TelemetryMessage:
        telemetry = TelemetryMessage(**payload.model_dump())
        self.db.add(telemetry)
        await self.db.flush()
        await self.db.refresh(telemetry)

        # Broadcast the new telemetry point
        await manager.broadcast({
            "type": "telemetry",
            "data": {
                "id": str(telemetry.id),
                "node_id": str(telemetry.node_id) if telemetry.node_id else None,
                "shipment_id": str(telemetry.shipment_id) if telemetry.shipment_id else None,
                "type": telemetry.type,
                "payload": telemetry.payload,
                "created_at": telemetry.created_at.isoformat()
            }
        })
        return telemetry

