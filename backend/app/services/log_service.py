from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog, AgentLogStatus
from app.schemas.agent_log import AgentLogCreate
from app.api.websocket_manager import manager


class LogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_log(self, payload: AgentLogCreate) -> AgentLog:
        # Resolve status enum if it's a string
        status_val = payload.status
        if isinstance(status_val, str):
            try:
                status_val = AgentLogStatus(status_val.lower())
            except ValueError:
                status_val = AgentLogStatus.SUCCESS

        log_data = payload.model_dump()
        log_data["status"] = status_val

        log = AgentLog(**log_data)
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)

        # Broadcast the new log to all WebSocket clients
        await manager.broadcast("dashboard", {
            "type": "log",
            "data": {
                "id": str(log.id),
                "agent_name": log.agent_name,
                "agent_type": log.agent_type,
                "action_type": log.action_type,
                "status": log.status.value,
                "message": log.message,
                "payload": log.payload,
                "result": log.result,
                "confidence": float(log.confidence) if log.confidence is not None else None,
                "executed_at": log.executed_at.isoformat()
            }
        })
        return log

    async def get_logs(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[AgentLog]:
        query = select(AgentLog).order_by(AgentLog.executed_at.desc())

        if since:
            query = query.where(AgentLog.executed_at >= since)
        if agent_name:
            query = query.where(AgentLog.agent_name.ilike(f"%{agent_name}%"))
        if agent_type:
            query = query.where(AgentLog.agent_type == agent_type)
        if status:
            try:
                enum_status = AgentLogStatus(status.lower())
                query = query.where(AgentLog.status == enum_status)
            except ValueError:
                pass
        if search:
            query = query.where(
                or_(
                    AgentLog.message.ilike(f"%{search}%"),
                    AgentLog.agent_name.ilike(f"%{search}%"),
                    AgentLog.agent_type.ilike(f"%{search}%"),
                    AgentLog.action_type.ilike(f"%{search}%"),
                )
            )

        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
