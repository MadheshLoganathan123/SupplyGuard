"""
Reports, exports, and analytics API endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.reports import (
    AgentPerformanceRead,
    ExportJobCreate,
    ExportJobRead,
    ExportJobResponse,
    ReportsMetrics,
)
from app.services.reporting_service import ReportingService, run_export_job

router = APIRouter()


@router.get("/metrics", response_model=ReportsMetrics, summary="Reports dashboard metrics")
async def get_reports_metrics(db: AsyncSession = Depends(get_db)):
    return await ReportingService(db).get_metrics()


@router.get("/agents/performance", response_model=list[AgentPerformanceRead], summary="Agent performance list")
async def list_agent_performance(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await ReportingService(db).list_agent_performances(limit=limit)


@router.post(
    "/export",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate audit report export",
)
async def create_export(
    background_tasks: BackgroundTasks,
    fmt: str = Query("json", pattern="^(pdf|xls|json)$"),
    payload: ExportJobCreate | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = payload.query if payload else {}
    job = await ReportingService(db).create_export_job(fmt, query)
    await db.commit()
    background_tasks.add_task(run_export_job, job.id)
    return ExportJobResponse(job_id=job.id, format=fmt, status=job.status)


@router.get("/export/{job_id}", summary="Get export job status and data")
async def get_export(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await ReportingService(db).get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found")

    response = ExportJobRead.model_validate(job)
    if job.format == "json" and job.result_data:
        return JSONResponse(content={
            **response.model_dump(mode="json"),
            "download": job.result_data,
        })
    return response
