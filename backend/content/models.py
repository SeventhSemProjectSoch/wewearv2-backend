import uuid
from typing import Optional

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

from users.models import Theme
from users.models import User

UserModel = settings.AUTH_USER_MODEL
media_storage = FileSystemStorage(location="media/posts")


class Post(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="posts"
    )
    media_url = models.URLField(blank=True, null=True)
    media_file = models.FileField(
        upload_to="posts/",
        storage=media_storage,
        blank=True,
        null=True,
    )

    caption = models.TextField(blank=True, null=True)
    themes = models.ManyToManyField(Theme, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)

    def media(self) -> str:
        if self.media_file:
            return self.media_file.url
        return self.media_url or ""

    def __str__(self) -> str:
        return (
            f"{self.author.username or self.author.id} - {self.caption[:20]}"
        )


class Follow(models.Model):
    id = models.BigAutoField(primary_key=True)
    follower = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")


class Like(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")


class Save(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="saves"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="saves"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")


class Comment(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="comments"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Share(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="shares"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="shares"
    )
    slug = models.CharField(max_length=8, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = uuid.uuid4().hex[:8]
        super().save(*args, **kwargs)


class Impression(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="impressions"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="impressions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "post"]),
        ]
