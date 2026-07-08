"""
Demand projection job API endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles
from app.database.session import get_db
from app.schemas.projection import ProjectionCreate, ProjectionJobResponse, ProjectionRead
from app.schemas.user import UserRole
from app.services.projection_service import ProjectionService, run_projection_job

router = APIRouter()


@router.post(
    "/",
    response_model=ProjectionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run demand projection",
)
async def create_projection(
    payload: ProjectionCreate,
    background_tasks: BackgroundTasks,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN, UserRole.FARMER, UserRole.STORE_OWNER])),
    db: AsyncSession = Depends(get_db),
):
    projection = await ProjectionService(db).create(payload)
    await db.commit()
    background_tasks.add_task(run_projection_job, projection.id)
    return ProjectionJobResponse(job_id=projection.id)


@router.get("/{projection_id}", response_model=ProjectionRead, summary="Get projection result")
async def get_projection(projection_id: str, db: AsyncSession = Depends(get_db)):
    projection = await ProjectionService(db).get_by_id(projection_id)
    if not projection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projection not found")
    return projection
