"""
Agents API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.schemas.reports import AgentPerformanceRead
from app.services.agent_service import AgentService
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get("/", response_model=List[AgentRead])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    svc = AgentService(db)
    if active_only:
        return await svc.get_active()
    return await svc.get_all(skip=skip, limit=limit)


@router.get("/{agent_id}/performance", response_model=AgentPerformanceRead)
async def get_agent_performance(agent_id: str, db: AsyncSession = Depends(get_db)):
    perf = await ReportingService(db).get_agent_performance(agent_id)
    if not perf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return perf


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    svc = AgentService(db)
    agent = await svc.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await AgentService(db).create(payload)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str, payload: AgentUpdate, db: AsyncSession = Depends(get_db)
):
    svc = AgentService(db)
    agent = await svc.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return await svc.update(agent, payload)
