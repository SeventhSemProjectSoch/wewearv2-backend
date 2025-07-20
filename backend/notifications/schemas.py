from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    type: str
    actor_username: str
    post_id: int | None = None
    created_at: datetime
    read: bool


class NotificationMarkIn(BaseModel):
    read: bool
