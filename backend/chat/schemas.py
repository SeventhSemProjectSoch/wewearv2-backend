from datetime import datetime
from typing import Annotated

from annotated_types import MaxLen
from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    sender_id: str
    receiver_id: str
    content: str
    created_at: datetime
    read: bool


class MessageIn(BaseModel):
    receiver_id: str
    content: Annotated[str, MaxLen(1500)]


class ConversationOut(BaseModel):
    user_id: str
    username: str
    last_message: str
    last_timestamp: datetime
