from datetime import datetime
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.services.log_service import LogService


class AgentLogService(LogService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_recent(self, limit: int = 50, since: Optional[datetime] = None) -> List[AgentLog]:
        return await self.get_logs(limit=limit, since=since)

