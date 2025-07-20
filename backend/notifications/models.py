from django.db import models

from content.models import BaseModel
from content.models import Post
from users.models import User


class Notification(BaseModel):
    class NotificationType(models.TextChoices):
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        SHARE = "share", "Share"
        FOLLOW = "follow", "Follow"

    recipient: models.ForeignKey[User, User] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    actor: models.ForeignKey[User, User] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sent"
    )
    type: models.CharField[str, str] = models.CharField(
        max_length=10, choices=NotificationType.choices
    )
    post: models.ForeignKey[Post, Post] = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifications",
    )
    read: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.actor} {self.type} → {self.recipient}"
