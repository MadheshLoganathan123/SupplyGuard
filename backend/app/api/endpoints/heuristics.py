"""
Agent heuristics tuning API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.heuristic import HeuristicCreate, HeuristicRead
from app.services.heuristics_service import HeuristicsService

router = APIRouter()


@router.get("/", response_model=List[HeuristicRead], summary="List heuristics settings")
async def list_heuristics(db: AsyncSession = Depends(get_db)):
    return await HeuristicsService(db).get_all()


@router.post(
    "/",
    response_model=HeuristicRead,
    status_code=201,
    summary="Save heuristics settings",
)
async def save_heuristics(
    payload: HeuristicCreate,
    db: AsyncSession = Depends(get_db),
):
    heuristic = await HeuristicsService(db).create(payload)
    await db.commit()
    return heuristic
