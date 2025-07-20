import uuid
from datetime import datetime
from typing import Any

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from users.models import Theme

UserModel = settings.AUTH_USER_MODEL
media_storage = FileSystemStorage(location="media/posts")


class BaseModel(models.Model):
    id: models.BigAutoField[int, int] = models.BigAutoField(primary_key=True)
    created_at: models.DateTimeField[
        datetime, datetime
    ] = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Post(BaseModel):
    author: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="posts"
    )
    media_url: models.CharField[str, str | None] = models.URLField(
        blank=True, null=True
    )
    media_file: models.FileField = models.FileField(
        upload_to="posts/",
        storage=media_storage,
        blank=True,
        null=True,
    )

    caption: models.TextField[str, str | None] = models.TextField(
        blank=True, null=True, db_index=True
    )
    themes: models.ManyToManyField[Theme, Theme] = models.ManyToManyField(
        Theme, related_name="posts"
    )

    def media(self) -> str:
        if self.media_file:
            return self.media_file.url
        return self.media_url or ""

    def __str__(self) -> str:
        return f"{self.author.username or self.author.id} - {self.caption[:20] if self.caption else ''}"


class Follow(BaseModel):
    follower: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="following"
    )
    following: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="followers"
    )

    class Meta(BaseModel.Meta):
        unique_together = ("follower", "following")


class Like(BaseModel):
    user: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="likes"
    )
    post: models.ForeignKey[
        Post,
        Post,
    ] = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta(BaseModel.Meta):
        unique_together = ("user", "post")


class Save(BaseModel):
    user: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="saves"
    )
    post: models.ForeignKey[
        Post,
        Post,
    ] = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")

    class Meta(BaseModel.Meta):
        unique_together = ("user", "post")


class Comment(BaseModel):
    user: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="comments"
    )
    post: models.ForeignKey[
        Post,
        Post,
    ] = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    text: models.TextField[str, str] = models.TextField()


class Share(BaseModel):
    user: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="shares"
    )
    post: models.ForeignKey[
        Post,
        Post,
    ] = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="shares"
    )
    slug: models.CharField[str, str] = models.CharField(
        max_length=8, unique=True, db_index=True
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = uuid.uuid4().hex[:8]
        super().save(*args, **kwargs)


class Impression(BaseModel):
    user: models.ForeignKey[
        UserModel,
        UserModel,
    ] = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="impressions"
    )
    post: models.ForeignKey[
        Post,
        Post,
    ] = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="impressions"
    )

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["user", "post"]),
        ]
