"""
Supply topology nodes API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.node import NodeDetail, NodeListResponse
from app.services.node_service import NodeService

router = APIRouter()


@router.get("/", response_model=NodeListResponse, summary="List topology nodes")
async def list_nodes(db: AsyncSession = Depends(get_db)):
    return await NodeService(db).list_nodes()


@router.get("/{node_id}", response_model=NodeDetail, summary="Get node detail")
async def get_node(node_id: str, db: AsyncSession = Depends(get_db)):
    detail = await NodeService(db).get_detail(node_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return detail
