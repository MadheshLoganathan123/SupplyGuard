from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    body: str = ""
    notification_type: str = "info"
    link: Optional[str] = None


class NotificationUpdate(BaseModel):
    read: bool = True


class NotificationRead(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    body: str
    notification_type: str
    read: bool
    link: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    total: int
    unread: int
    items: list[NotificationRead]
