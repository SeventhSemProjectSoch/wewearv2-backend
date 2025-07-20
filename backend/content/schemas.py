from datetime import datetime
from typing import Optional

from ninja import File
from ninja import Form
from ninja import Schema
from ninja.files import UploadedFile


class PostCreateSchema(Schema):
    caption: Optional[str] = None
    themes: list[int]
    media_url: Optional[Form[str]] = None
    media_file: Optional[File[UploadedFile]] = None


class PostSchema(Schema):
    id: int
    author_id: int
    author_username: Optional[str]
    media_url: str
    caption: Optional[str]
    themes: list[str]
    created_at: datetime

    likes_count: int
    comments_count: int
    saves_count: int
    shares_count: int

    liked: bool
    saved: bool


class CommentCreateSchema(Schema):
    post_id: int
    text: str


class CommentSchema(Schema):
    id: int
    user_id: int
    username: Optional[str]
    text: str
    created_at: datetime


class ShareCreateSchema(Schema):
    post_id: int


class ShareResponseSchema(Schema):
    slug: str


class PaginatedPostsSchema(Schema):
    posts: list[PostSchema]
    total: int
    offset: int
    limit: int
