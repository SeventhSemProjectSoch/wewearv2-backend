from datetime import datetime
from typing import Annotated

from annotated_types import MaxLen
from ninja import ModelSchema
from pydantic import BaseModel

from chat.models import Message


class MessageModelSchema(ModelSchema):
    class Meta:
        model = Message
        fields = "__all__"


class MessageIn(BaseModel):
    receiver_id: str
    content: Annotated[str, MaxLen(1500)]


class ConversationOut(BaseModel):
    user_id: str
    username: str
    last_message: str
    last_timestamp: datetime
    profile_url: str | None
