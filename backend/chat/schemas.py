from datetime import datetime
from typing import Annotated

from annotated_types import MaxLen
from pydantic import BaseModel
from pydantic import constr


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    created_at: datetime
    read: bool


class MessageIn(BaseModel):
    receiver_id: int
    content: Annotated[str, MaxLen(1500)]


class ConversationOut(BaseModel):
    user_id: int
    username: str
    last_message: str
    last_timestamp: datetime
