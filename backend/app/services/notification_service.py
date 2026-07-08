"""
Notification service — create/query/dismiss user-facing notifications.
"""

import logging
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_for_user(
        self,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> Sequence[Notification]:
        q = select(Notification).order_by(Notification.created_at.desc())
        if user_id:
            q = q.where(Notification.user_id == user_id)
        if unread_only:
            q = q.where(Notification.read == False)
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def count_unread(self, user_id: str | None = None) -> int:
        q = select(func.count()).select_from(Notification).where(Notification.read == False)
        if user_id:
            q = q.where(Notification.user_id == user_id)
        return (await self.db.scalar(q)) or 0

    async def count_total(self, user_id: str | None = None) -> int:
        q = select(func.count()).select_from(Notification)
        if user_id:
            q = q.where(Notification.user_id == user_id)
        return (await self.db.scalar(q)) or 0

    async def create(self, payload: NotificationCreate) -> Notification:
        notif = Notification(**payload.model_dump())
        self.db.add(notif)
        await self.db.flush()
        await self.db.refresh(notif)
        return notif

    async def mark_read(self, notification_id: str) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return None
        notif.read = True
        notif.read_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(notif)
        return notif

    async def mark_all_read(self, user_id: str | None = None) -> int:
        q = (
            update(Notification)
            .values(read=True, read_at=datetime.now(timezone.utc))
            .where(Notification.read == False)
        )
        if user_id:
            q = q.where(Notification.user_id == user_id)
        result = await self.db.execute(q)
        return result.rowcount

    async def delete(self, notification_id: str) -> bool:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        await self.db.delete(notif)
        await self.db.flush()
        return True
