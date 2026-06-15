"""
Agent service — business logic for logistics agents.
"""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Agent]:
        result = await self.db.execute(
            select(Agent).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_by_id(self, agent_id: str) -> Agent | None:
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> Sequence[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.status == AgentStatus.ACTIVE)
        )
        return result.scalars().all()

    async def create(self, payload: AgentCreate) -> Agent:
        agent = Agent(**payload.model_dump())
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def update(self, agent: Agent, payload: AgentUpdate) -> Agent:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(agent, field, value)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent
