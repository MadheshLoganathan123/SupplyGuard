"""
Notifications API endpoints — user-facing alerts with bell integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthUser, require_roles, get_current_user
from app.database.session import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationRead,
    NotificationUpdate,
)
from app.schemas.user import UserRole
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=NotificationListResponse, summary="List notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    items = await svc.get_for_user(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )
    total = await svc.count_total(user_id=current_user.id)
    unread = await svc.count_unread(user_id=current_user.id)
    return NotificationListResponse(total=total, unread=unread, items=list(items))


@router.post(
    "/",
    response_model=NotificationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification",
)
async def create_notification(
    payload: NotificationCreate,
    current_user: AuthUser = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    return await NotificationService(db).create(payload)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark a notification as read",
)
async def mark_read(
    notification_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    notif = await svc.mark_read(notification_id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notif


@router.post(
    "/read-all",
    summary="Mark all notifications as read",
)
async def mark_all_read(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await NotificationService(db).mark_all_read(user_id=current_user.id)
    await db.commit()
    return {"marked_read": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: str,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await NotificationService(db).delete(notification_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
