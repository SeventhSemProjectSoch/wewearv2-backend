from datetime import datetime

from ninja import File
from ninja import Form
from ninja import Schema
from ninja.files import UploadedFile


class PostCreateSchema(Schema):
    caption: str | None = None
    themes: list[int]
    media_url: Form[str] | None = None
    media_file: File[UploadedFile] | None = None


class PostSchema(Schema):
    id: int
    author_id: str
    author_username: str
    media_url: str | None
    caption: str | None
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
    user_id: str
    username: str
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
