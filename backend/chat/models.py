from django.db import models

from core.models import BaseModel
from users.models import User


class Message(BaseModel):
    sender: models.ForeignKey[User, User] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver: models.ForeignKey[User, User] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    content: models.TextField[str, str] = models.TextField(max_length=1500)
    read: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["sender", "receiver", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender} → {self.receiver}: {self.content[:20]}"
