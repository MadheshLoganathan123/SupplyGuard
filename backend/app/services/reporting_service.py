import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.agent import Agent
from app.models.agent_performance import AgentPerformance
from app.models.export_job import ExportJob, ExportStatus
from app.models.incident import Incident
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.reports import AgentPerformanceRead, ReportsMetrics

logger = logging.getLogger(__name__)


class ReportingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_metrics(self) -> ReportsMetrics:
        incident_count = await self.db.scalar(select(func.count()).select_from(Incident)) or 0
        rerouted = await self.db.scalar(
            select(func.count()).where(Shipment.status == ShipmentStatus.REROUTED)
        ) or 0

        return ReportsMetrics(
            food_security_gaps_prevented=12400 + incident_count * 120,
            food_security_trend_pct=8.2,
            price_stability_variance_pct=1.4,
            tons_rerouted=842 + rerouted * 12,
            reroute_capacity_pct=min(100.0, 74 + rerouted),
            resilience_index=0.92,
            last_sync=datetime.now(timezone.utc),
        )

    async def get_agent_performance(self, agent_id: str) -> Optional[AgentPerformanceRead]:
        agent = await self.db.get(Agent, agent_id)
        if not agent:
            return None

        result = await self.db.execute(
            select(AgentPerformance)
            .where(AgentPerformance.agent_id == agent_id)
            .order_by(AgentPerformance.recorded_at.desc())
            .limit(1)
        )
        perf = result.scalar_one_or_none()
        metrics = perf.metrics if perf else {}

        return AgentPerformanceRead(
            agent_id=agent.id,
            name=agent.name,
            efficiency_pct=metrics.get("efficiency_pct", agent.efficiency_score),
            negotiation_speed_avg_sec=metrics.get("negotiation_speed_avg_sec", 1.5),
            route_accuracy_pct=metrics.get("route_accuracy_pct", 90.0),
            badge=metrics.get("badge"),
            recorded_at=perf.recorded_at if perf else None,
        )

    async def list_agent_performances(self, limit: int = 10) -> List[AgentPerformanceRead]:
        result = await self.db.execute(
            select(Agent)
            .order_by(Agent.efficiency_score.desc())
            .limit(limit)
        )
        agents = list(result.scalars().all())
        performances: List[AgentPerformanceRead] = []
        for agent in agents:
            perf = await self.get_agent_performance(agent.id)
            if perf:
                performances.append(perf)
        return performances

    async def create_export_job(self, fmt: str, query: dict) -> ExportJob:
        job = ExportJob(format=fmt, query=query, status=ExportStatus.QUEUED.value)
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_export_job(self, job_id: str) -> Optional[ExportJob]:
        return await self.db.get(ExportJob, job_id)


async def run_export_job(job_id: str) -> None:
    logger.info("Starting export job %s", job_id)
    await asyncio.sleep(1)

    async with AsyncSessionLocal() as db:
        svc = ReportingService(db)
        job = await svc.get_export_job(job_id)
        if not job:
            return

        job.status = ExportStatus.RUNNING.value
        await db.commit()

    await asyncio.sleep(1)

    async with AsyncSessionLocal() as db:
        svc = ReportingService(db)
        job = await svc.get_export_job(job_id)
        if not job:
            return

        incidents_result = await db.execute(
            select(Incident).order_by(Incident.occurred_at.desc()).limit(50)
        )
        incidents = list(incidents_result.scalars().all())
        metrics = await svc.get_metrics()
        performances = await svc.list_agent_performances()

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics.model_dump(mode="json"),
            "incidents": [
                {
                    "id": i.id,
                    "title": i.title,
                    "description": i.description,
                    "sector": i.sector,
                    "severity": i.severity.value if hasattr(i.severity, "value") else str(i.severity),
                    "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                    "occurred_at": i.occurred_at.isoformat(),
                }
                for i in incidents
            ],
            "agent_performance": [p.model_dump(mode="json") for p in performances],
        }

        job.status = ExportStatus.DONE.value
        job.result_data = payload
        job.finished_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Export job %s completed", job_id)
